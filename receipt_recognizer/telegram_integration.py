"""
Telegram integration for receipt-recognizer-client.
"""

import os
import asyncio
import tempfile
import logging
from typing import Optional, Dict, Any, Union
from pathlib import Path

from telegram import Update, PhotoSize
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
)
from telegram.constants import ParseMode

from .client import ReceiptRecognizerClient

logger = logging.getLogger(__name__)

# Hardcoded environment variable names
ENV_TELEGRAM_BOT_TOKEN = "TELEGRAM_BOT_TOKEN"
ENV_AUDIT_CHAT_ID = "TELEGRAM_AUDIT_CHAT_ID"
# Client variables (same as in client.py)
ENV_API_URL = "RECEIPT_RECOGNIZER_API_URL"
ENV_CLIENT_TOKEN = "RECEIPT_RECOGNIZER_CLIENT_TOKEN"


# ============================================
# OPTION 1: Process photo and return result
# ============================================

async def process_receipt_photo(
    update: Update,
    context: CallbackContext,
    recognizer: ReceiptRecognizerClient
) -> Dict[str, Any]:
    """
    Process receipt photo and return recognition result.
    For use in existing bots - you handle the response yourself.
    """
    try:
        # Get photo
        if update.message.photo:
            photo: PhotoSize = update.message.photo[-1]
            suffix = ".jpg"
        elif update.message.document:
            document = update.message.document
            if not document.mime_type.startswith('image/'):
                return {
                    'success': False,
                    'error': 'File is not an image'
                }
            photo = document
            suffix = Path(document.file_name).suffix or ".jpg"
        else:
            return {
                'success': False,
                'error': 'Unknown message type'
            }

        # Download photo
        temp_file = await _download_telegram_file(
            context.bot,
            photo.file_id,
            suffix
        )

        if not temp_file:
            return {
                'success': False,
                'error': 'Failed to download file'
            }

        # Recognize receipt
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                recognizer.recognize,
                str(temp_file)
            )

            return {
                'success': True,
                'data': result,
                'original_file': temp_file
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'original_file': temp_file
            }

    except Exception as e:
        return {
            'success': False,
            'error': f"Processing error: {str(e)}"
        }


def format_receipt_for_telegram(result: Dict[str, Any]) -> str:
    """Format receipt data for Telegram message"""
    if not result.get('success'):
        return f"❌ Error: {result.get('error', 'Unknown error')}"

    data = result['data']
    lines = ["✅ Receipt recognized", ""]

    # Format only fields that exist
    field_labels = {
        'source': '👤 Sender',
        'destination': '👥 Recipient',
        'amount': '💰 Amount',
        'fee': '📊 Fee',
        'date': '📅 Date',
        'bank': '🏦 Bank',
        'status': '✅ Status',
        'document_number': '📄 Doc number'
    }

    for field, label in field_labels.items():
        if field in data and data[field]:
            value = data[field]
            if field in ['amount', 'fee']:
                value = f"{float(value):.2f} RUB"
            lines.append(f"{label}: {value}")

    return "\n".join(lines)


# ============================================
# OPTION 2: Minimal bot for forwarding to audit
# ============================================

class ForwardingReceiptBot:
    """
    Minimal bot that forwards receipts to audit chat.

    Only does:
    1. Receives receipt photo from user
    2. Recognizes it
    3. Forwards original photo + recognition result to audit chat
    """

    def __init__(
        self,
        bot_token: Optional[str] = None,
        api_url: Optional[str] = None,
        client_token: Optional[str] = None,
        audit_chat_id: Optional[Union[str, int]] = None
    ):
        """
        Args (all optional, will be taken from environment if not provided):
            bot_token: Telegram Bot Token
            api_url: Receipt Recognizer API URL
            client_token: Client token for API
            audit_chat_id: Chat ID to forward receipts to
        """
        # Get values from environment if not provided
        self.bot_token = bot_token or os.getenv(ENV_TELEGRAM_BOT_TOKEN)
        self.audit_chat_id = audit_chat_id or os.getenv(ENV_AUDIT_CHAT_ID)

        if not self.bot_token:
            raise ValueError(
                f"Telegram bot token is required. "
                f"Set it as parameter or {ENV_TELEGRAM_BOT_TOKEN} environment variable."
            )

        if not self.audit_chat_id:
            raise ValueError(
                f"Audit chat ID is required. "
                f"Set it as parameter or {ENV_AUDIT_CHAT_ID} environment variable."
            )

        # Create recognizer client (it will get its own env vars)
        self.recognizer = ReceiptRecognizerClient(
            api_url=api_url,
            client_token=client_token
        )

    async def _forward_to_audit(
        self,
        update: Update,
        context: CallbackContext,
        result: Dict[str, Any]
    ) -> None:
        """Forward original photo and recognition result to audit chat"""
        try:
            user = update.effective_user
            message = update.message

            # Header with user info
            audit_header = (
                f"🧾 Receipt from @{user.username or user.first_name}\n"
                f"ID: {user.id}\n"
                f"Time: {message.date.strftime('%Y-%m-%d %H:%M:%S')}\n"
            )

            # 1. Forward original photo
            if message.photo:
                await context.bot.send_photo(
                    chat_id=self.audit_chat_id,
                    photo=message.photo[-1].file_id,
                    caption=audit_header
                )
            elif message.document:
                await context.bot.send_document(
                    chat_id=self.audit_chat_id,
                    document=message.document.file_id,
                    caption=audit_header
                )

            # 2. Send recognition result
            result_text = format_receipt_for_telegram(result)
            await context.bot.send_message(
                chat_id=self.audit_chat_id,
                text=f"Recognition result:\n\n{result_text}",
                parse_mode=ParseMode.HTML
            )

        except Exception as e:
            logger.error(f"Error forwarding to audit: {e}")

    async def _handle_photo(self, update: Update, context: CallbackContext) -> None:
        """Handle receipt photo from user"""
        user_msg = await update.message.reply_text("⏳ Processing receipt...")

        try:
            # Process receipt
            result = await process_receipt_photo(update, context, self.recognizer)

            # Send result to user
            result_text = format_receipt_for_telegram(result)
            await user_msg.edit_text(result_text)

            # Forward to audit chat
            await self._forward_to_audit(update, context, result)

        except Exception as e:
            await user_msg.edit_text(f"❌ Error: {str(e)}")
            logger.error(f"Error processing receipt: {e}")

    def run(self) -> None:
        """Run the bot in polling mode"""
        # Create minimal application
        application = (
            ApplicationBuilder()
            .token(self.bot_token)
            .build()
        )

        # Only handle photos
        application.add_handler(MessageHandler(
            filters.PHOTO | filters.Document.IMAGE,
            self._handle_photo
        ))

        # Start command
        async def start(update: Update, context: CallbackContext):
            await update.message.reply_text(
                "Send receipt photo for recognition. "
                "Result will be forwarded to audit chat."
            )

        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", start))

        logger.info("Starting ForwardingReceiptBot...")
        application.run_polling()


# ============================================
# Factory function
# ============================================

def create_forwarding_bot(
    bot_token: Optional[str] = None,
    api_url: Optional[str] = None,
    client_token: Optional[str] = None,
    audit_chat_id: Optional[Union[str, int]] = None
) -> ForwardingReceiptBot:
    """
    Factory function to create a forwarding bot.
    All parameters are optional and will be taken from environment if not provided.
    """
    return ForwardingReceiptBot(
        bot_token=bot_token,
        api_url=api_url,
        client_token=client_token,
        audit_chat_id=audit_chat_id
    )


# ============================================
# Utility functions
# ============================================

async def _download_telegram_file(bot, file_id: str, suffix: str) -> Optional[Path]:
    """Download file from Telegram to temporary file"""
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            temp_path = Path(tmp.name)

        file = await bot.get_file(file_id)
        await file.download_to_drive(temp_path)

        return temp_path
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        return None


# ============================================
# CLI entry point
# ============================================

def main():
    """CLI entry point for forwarding bot"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Telegram bot that forwards receipts to audit chat"
    )

    # All arguments are optional - will fall back to environment variables
    parser.add_argument(
        "--bot-token",
        help=f"Telegram Bot Token (env: {ENV_TELEGRAM_BOT_TOKEN})"
    )

    parser.add_argument(
        "--api-url",
        help=f"Receipt Recognizer API URL (env: {ENV_API_URL})"
    )

    parser.add_argument(
        "--client-token",
        help=f"Client token for API (env: {ENV_CLIENT_TOKEN})"
    )

    parser.add_argument(
        "--audit-chat-id",
        help=f"Chat ID to forward receipts to (env: {ENV_AUDIT_CHAT_ID})"
    )

    args = parser.parse_args()

    # Create and run bot
    bot = create_forwarding_bot(
        bot_token=args.bot_token,
        api_url=args.api_url,
        client_token=args.client_token,
        audit_chat_id=args.audit_chat_id
    )

    bot.run()


if __name__ == "__main__":
    main()