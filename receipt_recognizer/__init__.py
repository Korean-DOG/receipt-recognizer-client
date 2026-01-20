"""
Receipt Recognizer Client
"""

from .client import ReceiptRecognizerClient
from .constants import (
    BASE_FIELDS,
    SOURCE,
    DESTINATION,
    AMOUNT,
    FEE,
    DATE,
    BASE_FIELDS_DESC,
)
from .exceptions import (
    ReceiptRecognizerError,
    APIError,
    ValidationError,
    VersionMismatchError,
    DeprecatedClientError,
)
from .version import __version__, check_compatibility

__all__ = [
    "ReceiptRecognizerClient",
    "BASE_FIELDS",
    "SOURCE",
    "DESTINATION",
    "AMOUNT",
    "FEE",
    "DATE",
    "BASE_FIELDS_DESC",
    "__version__",
    "check_compatibility",
    "ReceiptRecognizerError",
    "APIError",
    "ValidationError",
    "VersionMismatchError",
    "DeprecatedClientError",
]

# Опциональная Telegram интеграция
try:
    from .telegram_integration import TelegramReceiptBot, create_telegram_client
    __all__.extend(["TelegramReceiptBot", "create_telegram_client"])
except ImportError:
    pass

# CLI интерфейс
try:
    from .cli import main as cli_main
    __all__.append("cli_main")
except ImportError:
    pass