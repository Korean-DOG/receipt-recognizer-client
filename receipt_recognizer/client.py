import os
import requests
import json
from pathlib import Path
from typing import Dict, Any, Optional
from .constants import BASE_FIELDS
from .exceptions import APIError, ValidationError, VersionMismatchError
from .version import __version__, MIN_SERVER_VERSION, check_compatibility
from .pdf_processor import PDFProcessor, process_receipt_pdf


class ReceiptRecognizerClient:
    """Клиент для работы с receipt-recognizer API"""

    # Hardcoded environment variable names with prefix
    ENV_API_URL = "RECEIPT_RECOGNIZER_API_URL"
    ENV_CLIENT_TOKEN = "RECEIPT_RECOGNIZER_CLIENT_TOKEN"

    def __init__(
            self,
            api_url: Optional[str] = None,
            client_token: Optional[str] = None,
            timeout: int = 30,
            verify_ssl: bool = True,
            process_pdf_locally: bool = True  # Включаем локальную обработку PDF
    ):
        """
        Args:
            api_url: URL API сервера (если None, берётся из env RECEIPT_RECOGNIZER_API_URL)
            client_token: Токен клиента (если None, берётся из env RECEIPT_RECOGNIZER_CLIENT_TOKEN)
            timeout: Таймаут запросов в секундах
            verify_ssl: Проверять SSL сертификаты
            process_pdf_locally: Обрабатывать PDF локально (True) или отправлять на сервер (False)
        """
        # Get values from environment if not provided
        self.api_url = (api_url or os.getenv(self.ENV_API_URL, "")).rstrip('/')
        self.client_token = client_token or os.getenv(self.ENV_CLIENT_TOKEN)
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.process_pdf_locally = process_pdf_locally

        # Если API URL не указан, работаем только в локальном режиме
        if not self.api_url:
            self.local_mode = True
            print("⚠️ Working in local mode (PDF processing only)")
        else:
            self.local_mode = False
            if not self.client_token:
                raise ValueError(
                    f"Client token is required when using API. "
                    f"Set it as parameter or {self.ENV_CLIENT_TOKEN} environment variable."
                )
            self._check_connection()

    def recognize(self, file_path: str | Path) -> Dict[str, Any]:
        """
        Распознает чек из файла (PDF или изображение).

        Args:
            file_path: Путь к файлу (PDF, JPG, PNG и т.д.)

        Returns:
            Словарь с данными чека

        Raises:
            APIError: Ошибка API
            ValidationError: Невалидные данные
        """
        file_path = Path(file_path)

        # Определяем тип файла
        is_pdf = file_path.suffix.lower() == '.pdf'

        # Если PDF и разрешена локальная обработка
        if is_pdf and (self.process_pdf_locally or self.local_mode):
            return self._process_pdf_locally(file_path)

        # Иначе отправляем на сервер (для изображений или если отключена локальная обработка PDF)
        return self._send_to_api(file_path)

    def _process_pdf_locally(self, pdf_path: Path) -> Dict[str, Any]:
        """Обрабатываем PDF локально"""
        try:
            # Проверяем, содержит ли PDF текст
            if not PDFProcessor.is_searchable_pdf(pdf_path):
                return {
                    'success': False,
                    'error': 'PDF содержит сканированное изображение. Требуется OCR.',
                    'source': 'pdf',
                    'is_scanned': True
                }

            # Извлекаем текст
            result = process_receipt_pdf(pdf_path, use_patterns=True)

            # Добавляем информацию об источнике
            result['source'] = 'pdf'
            result['is_scanned'] = False
            result['success'] = 'error' not in result

            # Если есть извлечённые данные, пытаемся сопоставить с базовыми полями
            if 'extracted' in result:
                extracted = result['extracted']

                # Маппинг на базовые поля
                mapped_result = {
                    'source': None,  # Будет извлекать из контекста
                    'destination': None,
                    'amount': extracted.get('amount'),
                    'fee': extracted.get('commission'),
                    'date': self._combine_date_time(extracted.get('date'), extracted.get('time')),
                    'bank': result.get('bank'),
                    'raw_extracted': extracted
                }

                # Добавляем в результат
                result['mapped'] = mapped_result

            return result

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'source': 'pdf'
            }

    def _send_to_api(self, file_path: Path) -> Dict[str, Any]:
        """Отправляем файл на API сервер"""
        if self.local_mode:
            raise ValueError("API URL not configured. Cannot send file to server.")

        # Читаем файл
        with open(file_path, 'rb') as f:
            file_data = f.read()

        # Определяем тип контента
        if file_path.suffix.lower() == '.pdf':
            content_type = 'application/pdf'
            field_name = 'pdf'
        else:
            content_type = 'image/jpeg'  # Для изображений
            field_name = 'image'

        # Подготавливаем запрос
        files = {field_name: (file_path.name, file_data, content_type)}

        # Заголовки с клиентским токеном
        headers = {
            'X-Client-Token': self.client_token,
            'X-Client-Version': __version__,
        }

        try:
            # Отправляем запрос
            response = requests.post(
                f"{self.api_url}/api/v1/recognize",
                files=files,
                headers=headers,
                timeout=self.timeout,
                verify=self.verify_ssl
            )

            # Обрабатываем ответ
            if response.status_code != 200:
                error_data = response.json()
                raise APIError(
                    f"API Error {response.status_code}: {error_data.get('error', 'Unknown error')}"
                )

            result = response.json()

            # Проверяем обязательные поля
            self._validate_result(result.get('data', {}))

            return result.get('data', {})

        except requests.exceptions.RequestException as e:
            raise APIError(f"Network error: {str(e)}")
        except json.JSONDecodeError as e:
            raise APIError(f"Invalid JSON response: {str(e)}")

    def _check_connection(self):
        """Проверяет соединение и совместимость с сервером"""
        try:
            # Запрашиваем информацию о сервере
            response = requests.get(
                f"{self.api_url}/api/health",
                timeout=self.timeout,
                verify=self.verify_ssl
            )

            if response.status_code == 200:
                info = response.json()

                # Проверяем версию сервера
                server_version = info.get('version', '0.0.0')

                try:
                    check_compatibility(__version__, server_version)
                except VersionMismatchError:
                    # Логируем предупреждение, но не падаем
                    import warnings
                    warnings.warn(
                        f"Version mismatch: client {__version__}, server {server_version}",
                        DeprecationWarning
                    )

        except requests.exceptions.RequestException as e:
            # Не падаем, только логируем
            import logging
            logging.warning(f"Could not check server version: {e}")

    def _validate_result(self, result: Dict[str, Any]):
        """Проверяет наличие обязательных полей в результате"""
        missing_fields = []

        for field in BASE_FIELDS:
            if field not in result or result[field] is None:
                missing_fields.append(field)

        if missing_fields:
            raise ValidationError(
                f"Missing required fields: {', '.join(missing_fields)}"
            )

    @staticmethod
    def _combine_date_time(date_str: Optional[str], time_str: Optional[str]) -> Optional[str]:
        """Объединяет дату и время в строку ISO формата"""
        if not date_str:
            return None

        # Простая обработка даты
        if time_str:
            return f"{date_str}T{time_str}"
        return date_str