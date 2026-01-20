#!/usr/bin/env python3
"""
CLI интерфейс для receipt-recognizer-client
"""

import argparse
import json
import sys
from pathlib import Path

from .client import ReceiptRecognizerClient
from .exceptions import APIError, ValidationError, VersionMismatchError
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
        help="Распознать чек из изображения",
    )
    recognize_parser.add_argument(
        "image_path",
        type=Path,
        help="Путь к изображению чека",
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

    # Команда check-version
    version_parser = subparsers.add_parser(
        "check-version",
        help="Проверить совместимость версий",
    )
    version_parser.add_argument(
        "server_version",
        help="Версия сервера (например, 1.2.0)",
    )

    # Команда validate
    validate_parser = subparsers.add_parser(
        "validate",
        help="Валидировать JSON результат",
    )
    validate_parser.add_argument(
        "json_file",
        type=Path,
        help="Путь к JSON файлу с результатом",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "recognize":
            recognize_command(args)
        elif args.command == "check-version":
            check_version_command(args)
        elif args.command == "validate":
            validate_command(args)

    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)


def recognize_command(args):
    """Обработка команды recognize"""
    # Загружаем настройки из переменных окружения
    import os

    api_url = os.getenv("RECEIPT_RECOGNIZER_API_URL")
    client_token = os.getenv("CLIENT_TOKEN")

    if not api_url or not client_token:
        print(
            "Ошибка: Не установлены переменные окружения\n"
            "Установите:\n"
            "  RECEIPT_RECOGNIZER_API_URL - URL API сервера\n"
            "  CLIENT_TOKEN - токен клиента",
            file=sys.stderr,
        )
        sys.exit(1)

    # Проверяем существование файла
    if not args.image_path.exists():
        print(f"Ошибка: Файл не найден: {args.image_path}", file=sys.stderr)
        sys.exit(1)

    # Создаем клиент
    client = ReceiptRecognizerClient(
        api_url=api_url,
        client_token=client_token,
    )

    try:
        # Распознаем чек
        print(f"Распознаю чек из {args.image_path}...", file=sys.stderr)
        result = client.recognize(args.image_path)

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

    except APIError as e:
        print(f"Ошибка API: {e}", file=sys.stderr)
        sys.exit(1)
    except ValidationError as e:
        print(f"Ошибка валидации: {e}", file=sys.stderr)
        sys.exit(1)


def check_version_command(args):
    """Обработка команды check-version"""
    from .version import check_compatibility

    try:
        check_compatibility(__version__, args.server_version)
        print(f"✓ Версии совместимы: клиент {__version__}, сервер {args.server_version}")
    except VersionMismatchError as e:
        print(f"✗ {e}", file=sys.stderr)
        sys.exit(1)


def validate_command(args):
    """Обработка команды validate"""
    from .constants import BASE_FIELDS

    try:
        data = json.loads(args.json_file.read_text())

        missing_fields = []
        for field in BASE_FIELDS:
            if field not in data or data[field] is None:
                missing_fields.append(field)

        if missing_fields:
            print(f"✗ Отсутствуют обязательные поля: {', '.join(missing_fields)}")
            sys.exit(1)
        else:
            print("✓ JSON содержит все обязательные поля")

    except json.JSONDecodeError as e:
        print(f"✗ Невалидный JSON: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()