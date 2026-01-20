from typing import Dict, Any, Optional
from .constants import BASE_FIELDS, SOURCE, DESTINATION, AMOUNT, FEE, DATE

try:
    # Импортируем библиотеку из GitHub
    from receipt_recognizer import ReceiptRecognizer as ExternalRecognizer

    HAS_EXTERNAL_LIB = True
except ImportError:
    HAS_EXTERNAL_LIB = False
    ExternalRecognizer = None


class ReceiptRecognizerClient:
    """Клиент для работы с receipt-recognizer-client из GitHub"""

    def __init__(self, api_key: str = None, folder_id: str = None):
        """
        Args:
            api_key: Ключ Yandex Vision API (опционально, если уже настроен в библиотеке)
            folder_id: Folder ID в Yandex Cloud (опционально)
        """
        if not HAS_EXTERNAL_LIB:
            raise ImportError(
                "Для использования установите receipt-recognizer-client из GitHub:\n"
                "pip install git+https://github.com/Korean-DOG/receipt-recognizer-client.git"
            )

        # Инициализируем внешнюю библиотеку
        self.external_recognizer = ExternalRecognizer(api_key,
                                                      folder_id) if api_key and folder_id else ExternalRecognizer()

    def recognize(self, image_path: str) -> Dict[str, Any]:
        """
        Распознает чек из изображения и возвращает данные в стандартизированном формате

        Args:
            image_path: Путь к изображению чека

        Returns:
            Словарь с обязательными базовыми полями
        """
        try:
            # Получаем результат из внешней библиотеки
            result = self.external_recognizer.recognize(image_path)

            # Конвертируем в наш стандартизированный формат
            return self._standardize_result(result)

        except Exception as e:
            raise Exception(f"Ошибка при распознавании чека: {str(e)}")

    def _standardize_result(self, raw_result: Dict) -> Dict[str, Any]:
        """Конвертирует результат внешней библиотеки в наш стандартизированный формат"""

        # Извлекаем базовые поля из raw_result
        # Внешняя библиотека должна возвращать данные в предсказуемом формате
        # Настройте этот метод под формат, который возвращает receipt-recognizer-client

        standardized = {
            SOURCE: self._extract_field(raw_result, 'sender', 'sender_card', 'source'),
            DESTINATION: self._extract_field(raw_result, 'receiver', 'receiver_card', 'destination'),
            AMOUNT: self._extract_numeric_field(raw_result, 'amount', 'total', 'sum'),
            FEE: self._extract_numeric_field(raw_result, 'commission', 'fee'),
            DATE: self._extract_date_field(raw_result, 'date', 'datetime', 'time'),
            '_raw': raw_result  # Сохраняем оригинальный результат
        }

        # Проверяем наличие обязательных полей
        missing_fields = [field for field in BASE_FIELDS if standardized.get(field) is None]
        if missing_fields:
            raise ValueError(f"Не удалось извлечь обязательные поля: {missing_fields}")

        return standardized

    def _extract_field(self, data: Dict, *possible_keys: str) -> Optional[Any]:
        """Извлекает поле по нескольким возможным ключам"""
        for key in possible_keys:
            if key in data:
                return data[key]
        return None

    def _extract_numeric_field(self, data: Dict, *possible_keys: str) -> Optional[float]:
        """Извлекает числовое поле"""
        value = self._extract_field(data, *possible_keys)
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _extract_date_field(self, data: Dict, *possible_keys: str) -> Optional[str]:
        """Извлекает и форматирует поле даты"""
        value = self._extract_field(data, *possible_keys)
        if value is None:
            return None
        # Конвертируем в строку ISO формата, если это datetime
        if hasattr(value, 'isoformat'):
            return value.isoformat()
        return str(value)

    def validate_fields(self, result: Dict[str, Any]) -> bool:
        """Проверяет наличие всех обязательных полей"""
        return all(field in result and result[field] is not None for field in BASE_FIELDS)