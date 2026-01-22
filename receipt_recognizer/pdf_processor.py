"""
PDF processing module for receipt-recognizer-client.
Extracts text directly from PDF without OCR.
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import Dict, Any, Optional, List
import re


class PDFProcessor:
    """Process PDF files to extract text directly"""

    @staticmethod
    def extract_text_from_pdf(pdf_path: str | Path) -> str:
        """
        Extract all text from PDF with positions.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted text with basic positional info
        """
        text_lines = []

        try:
            with fitz.open(pdf_path) as doc:
                for page_num, page in enumerate(doc):
                    # Извлекаем текст с позициями
                    blocks = page.get_text("blocks")  # (x0, y0, x1, y1, text, block_no, block_type)

                    # Сортируем по позиции (сверху вниз, слева направо)
                    blocks.sort(key=lambda b: (b[1], b[0]))  # sort by y0, then x0

                    for block in blocks:
                        text = block[4].strip()
                        if text:
                            text_lines.append(text)

            return "\n".join(text_lines)

        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")

    @staticmethod
    def extract_text_with_positions(pdf_path: str | Path) -> List[Dict[str, Any]]:
        """
        Extract text with detailed positional information.

        Returns:
            List of dicts with text and its position on page
        """
        result = []

        try:
            with fitz.open(pdf_path) as doc:
                for page_num, page in enumerate(doc):
                    # Получаем слова с позициями
                    words = page.get_text("words")

                    # Группируем слова в строки
                    lines = {}
                    for word in words:
                        # word = (x0, y0, x1, y1, "word", block_no, line_no, word_no)
                        x0, y0, x1, y1, text, block_no, line_no, word_no = word

                        # Группируем по строкам (по координате y)
                        y_key = round(y0, 1)  # округляем для группировки
                        if y_key not in lines:
                            lines[y_key] = []

                        lines[y_key].append({
                            'text': text,
                            'x': x0,
                            'y': y0,
                            'width': x1 - x0,
                            'height': y1 - y0
                        })

                    # Сортируем строки по вертикальной позиции
                    for y_pos in sorted(lines.keys()):
                        # Сортируем слова в строке по горизонтальной позиции
                        line_words = sorted(lines[y_pos], key=lambda w: w['x'])
                        line_text = " ".join(w['text'] for w in line_words)

                        if line_text.strip():
                            result.append({
                                'page': page_num,
                                'y_position': y_pos,
                                'text': line_text,
                                'words': line_words
                            })

            return result

        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")

    @staticmethod
    def is_searchable_pdf(pdf_path: str | Path) -> bool:
        """
        Check if PDF contains selectable text (not scanned).

        Args:
            pdf_path: Path to PDF file

        Returns:
            True if PDF contains text, False if it's scanned image
        """
        try:
            with fitz.open(pdf_path) as doc:
                text = ""
                for page in doc[:3]:  # Check first 3 pages
                    text += page.get_text()

                # If we have substantial text, it's searchable
                return len(text.strip()) > 50

        except:
            return False

    @staticmethod
    def find_text_by_patterns(pdf_path: str | Path, patterns: Dict[str, str]) -> Dict[str, str]:
        """
        Find specific information in PDF using regex patterns.

        Args:
            pdf_path: Path to PDF file
            patterns: Dict with field names and regex patterns

        Returns:
            Dict with found values
        """
        text = PDFProcessor.extract_text_from_pdf(pdf_path)
        result = {}

        for field_name, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                # Извлекаем группу или весь матч
                result[field_name] = match.group(1) if match.groups() else match.group(0)
            else:
                result[field_name] = None

        return result


# Predefined patterns for receipt recognition
RECEIPT_PATTERNS = {
    'amount': r'(\d+[.,]\d{2})\s*(?:руб|RUB|₽|р\.)',
    'card_number': r'(\*\*\*\*\s*\d{4})',
    'date': r'(\d{1,2}[-./]\d{1,2}[-./]\d{2,4})',
    'time': r'(\d{1,2}:\d{2}(?::\d{2})?)',
    'operation_id': r'(?:№|#|номер)[\s:]*(\d+)',
    'commission': r'комисс(?:ия)?[\s:]*(\d+[.,]\d{2})',
}


def process_receipt_pdf(
        pdf_path: str | Path,
        use_patterns: bool = True
) -> Dict[str, Any]:
    """
    Process receipt PDF and extract structured information.

    Args:
        pdf_path: Path to PDF receipt
        use_patterns: Whether to use predefined patterns for extraction

    Returns:
        Structured receipt data
    """
    try:
        # Extract all text
        full_text = PDFProcessor.extract_text_from_pdf(pdf_path)

        # Extract with positions for better structure understanding
        positioned_text = PDFProcessor.extract_text_with_positions(pdf_path)

        result = {
            'full_text': full_text,
            'positioned_text': positioned_text,
            'is_searchable': PDFProcessor.is_searchable_pdf(pdf_path)
        }

        # Extract using patterns if requested
        if use_patterns:
            pattern_results = PDFProcessor.find_text_by_patterns(pdf_path, RECEIPT_PATTERNS)
            result['extracted'] = pattern_results

            # Try to identify bank
            text_lower = full_text.lower()
            if 'сбер' in text_lower or 'sber' in text_lower:
                result['bank'] = 'Сбербанк'
            elif 'тинькофф' in text_lower or 'tinkoff' in text_lower:
                result['bank'] = 'Тинькофф'
            elif 'альфа' in text_lower or 'alfa' in text_lower:
                result['bank'] = 'Альфа-банк'
            elif 'втб' in text_lower:
                result['bank'] = 'ВТБ'

        return result

    except Exception as e:
        return {
            'error': str(e),
            'success': False
        }