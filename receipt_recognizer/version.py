"""
Управление версиями для контроля совместимости
"""

# Версия клиентской библиотеки
__version__ = "1.0.0"

# Минимальная поддерживаемая версия сервера
MIN_SERVER_VERSION = "1.0.0"

# Формат версии API, которую понимает клиент
API_VERSION = "v1"


def check_compatibility(client_version: str, server_version: str) -> bool:
    """
    Проверяет совместимость версий

    Args:
        client_version: Версия клиента
        server_version: Версия сервера

    Returns:
        bool: True если совместимы

    Raises:
        Exception: Если версии несовместимы
    """
    # Простая проверка: major версия должна совпадать
    client_major = client_version.split('.')[0]
    server_major = server_version.split('.')[0]

    if client_major != server_major:
        raise Exception(
            f"Несовместимые версии. Клиент v{client_major}.x.x "
            f"не может работать с сервером v{server_major}.x.x. "
            f"Установите подходящую версию."
        )

    return True