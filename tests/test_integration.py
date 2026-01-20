"""Интеграционные тесты (требуют реального API)"""
import pytest
import os
from receipt_recognizer import ReceiptRecognizerClient


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("INTEGRATION_TEST"),
    reason="Требует настроенного API и токена"
)
class TestIntegration:
    def test_real_api_call(self):
        """Реальный вызов API (только для ручного тестирования)"""
        client = ReceiptRecognizerClient(
            api_url=os.getenv("RECEIPT_RECOGNIZER_API_URL"),
            client_token=os.getenv("CLIENT_TOKEN")
        )

        # Используем тестовое изображение
        test_image = os.path.join(
            os.path.dirname(__file__),
            "fixtures",
            "sample_receipt.jpg"
        )

        if os.path.exists(test_image):
            result = client.recognize(test_image)
            assert "amount" in result
            assert "source" in result
            print(f"Успешно! Распознанная сумма: {result['amount']}")