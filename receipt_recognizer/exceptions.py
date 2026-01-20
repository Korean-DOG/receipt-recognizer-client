"""
Исключения для обработки ошибок совместимости
"""


class ReceiptRecognizerError(Exception):
    """Базовое исключение"""
    pass


class APIError(ReceiptRecognizerError):
    """Ошибка API"""
    pass


class ValidationError(ReceiptRecognizerError):
    """Ошибка валидации данных"""
    pass


class VersionMismatchError(ReceiptRecognizerError):
    """Несовместимость версий клиента и сервера"""

    def __init__(self, client_version, server_version, message=""):
        self.client_version = client_version
        self.server_version = server_version
        self.message = message or (
            f"Version mismatch: client={client_version}, server={server_version}. "
            f"Please update your client library."
        )
        super().__init__(self.message)


class DeprecatedClientError(ReceiptRecognizerError):
    """Клиентская библиотека устарела"""
    pass