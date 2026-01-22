import os
import requests
import json
from pathlib import Path
from typing import Dict, Any, Optional
from .constants import BASE_FIELDS
from .version import __version__, check_compatibility


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
            verify_ssl: bool = True
    ):
        """
        Args:
            api_url: URL API сервера (если None, берётся из env RECEIPT_RECOGNIZER_API_URL)
            client_token: Токен клиента (если None, берётся из env RECEIPT_RECOGNIZER_CLIENT_TOKEN)
            timeout: Таймаут запросов в секундах
            verify_ssl: Проверять SSL сертификаты
        """
        # Get values from environment if not provided
        self.api_url = (api_url or os.getenv(self.ENV_API_URL, "")).rstrip('/')
        self.client_token = client_token or os.getenv(self.ENV_CLIENT_TOKEN)

        if not self.api_url:
            raise ValueError(
                f"API URL is required. "
                f"Set it as parameter or {self.ENV_API_URL} environment variable."
            )

        if not self.client_token:
            raise ValueError(
                f"Client token is required. "
                f"Set it as parameter or {self.ENV_CLIENT_TOKEN} environment variable."
            )

        self.timeout = timeout
        self.verify_ssl = verify_ssl

        # Проверяем соединение и совместимость при инициализации
        self._check_connection()

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
                except Exception as e:
                    # Логируем предупреждение, но не падаем
                    import warnings
                    warnings.warn(str(e), DeprecationWarning)

        except requests.exceptions.RequestException as e:
            # Не падаем, только логируем
            import logging
            logging.warning(f"Could not check server version: {e}")

    def recognize(self, image_path: str | Path) -> Dict[str, Any]:
        """
        Распознает чек из изображения

        Args:
            image_path: Путь к файлу изображения

        Returns:
            Словарь с данными чека

        Raises:
            Exception: Ошибка API или сети
        """
        # Читаем файл
        with open(image_path, 'rb') as f:
            image_data = f.read()

        # Подготавливаем запрос
        files = {'file': (Path(image_path).name, image_data)}

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
                raise Exception(
                    f"API Error {response.status_code}: {error_data.get('error', 'Unknown error')}"
                )

            result = response.json()

            # Проверяем обязательные поля
            self._validate_result(result.get('data', {}))

            return result.get('data', {})

        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response: {str(e)}")

    def _validate_result(self, result: Dict[str, Any]):
        """Проверяет наличие обязательных полей в результате"""
        missing_fields = []

        for field in BASE_FIELDS:
            if field not in result or result[field] is None:
                missing_fields.append(field)

        if missing_fields:
            raise ValueError(
                f"Missing required fields: {', '.join(missing_fields)}"
            )