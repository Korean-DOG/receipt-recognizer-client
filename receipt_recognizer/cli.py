#!/usr/bin/env python3
"""
CLI интерфейс для receipt-recognizer-client
"""

import argparse
import json
import sys
from pathlib import Path

from .client import ReceiptRecognizerClient
from .pdf_processor import PDFProcessor, process_receipt_pdf
from .version import __version__


def main():
    parser = argparse.ArgumentParser(
        description="Receipt Recognizer Client CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"receipt-recognizer-client v{__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Команды")

    # Команда recognize
    recognize_parser = subparsers.add_parser(
        "recognize",
        help="Распознать чек из файла (PDF или изображение)",
    )
    recognize_parser.add_argument(
        "file_path",
        type=Path,
        help="Путь к файлу (PDF, JPG, PNG)",
    )
    recognize_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Сохранить результат в файл (JSON)",
    )
    recognize_parser.add_argument(
        "--pretty",
        action="store_true",
        help="Красиво форматировать вывод",
    )
    recognize_parser.add_argument(
        "--local",
        action="store_true",
        help="Обработать PDF локально (без отправки на сервер)",
    )

    # Команда check-pdf
    pdf_parser = subparsers.add_parser(
        "check-pdf",
        help="Проверить PDF файл",
    )
    pdf_parser.add_argument(
        "pdf_path",
        type=Path,
        help="Путь к PDF файлу",
    )
    pdf_parser.add_argument(
        "--extract-text",
        action="store_true",
        help="Извлечь и показать текст",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "recognize":
            recognize_command(args)
        elif args.command == "check-pdf":
            check_pdf_command(args)

    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)


def recognize_command(args):
    """Обработка команды recognize"""
    # Проверяем существование файла
    if not args.file_path.exists():
        print(f"Ошибка: Файл не найден: {args.file_path}", file=sys.stderr)
        sys.exit(1)

    # Создаем клиент
    client = ReceiptRecognizerClient(
        process_pdf_locally=args.local or args.file_path.suffix.lower() == '.pdf'
    )

    try:
        # Распознаем чек
        print(f"Распознаю чек из {args.file_path}...", file=sys.stderr)
        result = client.recognize(args.file_path)

        # Форматируем вывод
        if args.pretty:
            output = json.dumps(result, ensure_ascii=False, indent=2)
        else:
            output = json.dumps(result, ensure_ascii=False)

        # Выводим результат
        if args.output:
            args.output.write_text(output, encoding="utf-8")
            print(f"Результат сохранен в {args.output}", file=sys.stderr)
        else:
            print(output)

    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)


def check_pdf_command(args):
    """Обработка команды check-pdf"""
    if not args.pdf_path.exists():
        print(f"Ошибка: Файл не найден: {args.pdf_path}", file=sys.stderr)
        sys.exit(1)

    try:
        # Проверяем PDF
        is_searchable = PDFProcessor.is_searchable_pdf(args.pdf_path)

        if args.extract_text:
            text = PDFProcessor.extract_text_from_pdf(args.pdf_path)
            print(f"Текст из PDF ({'поисковый' if is_searchable else 'скан'}):")
            print("-" * 50)
            print(text[:1000])  # Первые 1000 символов
            if len(text) > 1000:
                print(f"\n... и ещё {len(text) - 1000} символов")
        else:
            print(f"PDF файл: {args.pdf_path}")
            print(f"Содержит текст: {'Да' if is_searchable else 'Нет (требуется OCR)'}")

            if is_searchable:
                # Быстрый анализ
                result = process_receipt_pdf(args.pdf_path, use_patterns=False)
                print(f"Количество страниц: {len(result.get('positioned_text', []))}")
                print(f"Пример текста: {result.get('full_text', '')[:200]}...")

    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()