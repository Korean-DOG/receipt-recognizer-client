"""
Управление версиями для контроля совместимости
"""

# Версия клиентской библиотеки
__version__ = "1.0.0"

from receipt_recognizer import VersionMismatchError

# Минимальная поддерживаемая версия сервера
MIN_SERVER_VERSION = "1.0.0"

# Формат версии API, которую понимает клиент
API_VERSION = "v1"


def check_compatibility(client_version, server_version):
    """
    Проверяет совместимость версий

    Args:
        client_version: Версия клиента
        server_version: Версия сервера

    Returns:
        bool: True если совместимы

    Raises:
        VersionMismatchError: Если версии несовместимы
    """
    # Простая проверка: major версия должна совпадать
    client_major = client_version.split('.')[0]
    server_major = server_version.split('.')[0]

    if client_major != server_major:
        raise VersionMismatchError(
            client_version=client_version,
            server_version=server_version,
            message=(
                f"Incompatible versions. Client v{client_major}.x.x "
                f"cannot work with server v{server_major}.x.x. "
                f"Please install matching version."
            )
        )

    return True