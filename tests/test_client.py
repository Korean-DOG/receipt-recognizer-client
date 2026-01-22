"""Тесты основного клиента"""
import pytest
from unittest.mock import Mock, patch
import os


class TestReceiptRecognizerClient:
    def test_init_without_env_vars(self):
        """Инициализация без переменных окружения должна вызывать ошибку"""
        # Удаляем переменные окружения если они есть
        env_vars = ["RECEIPT_RECOGNIZER_API_URL", "RECEIPT_RECOGNIZER_CLIENT_TOKEN"]
        for var in env_vars:
            if var in os.environ:
                del os.environ[var]

        with pytest.raises(ValueError, match="API URL is required"):
            from receipt_recognizer import ReceiptRecognizerClient
            ReceiptRecognizerClient()

    def test_init_with_env_vars(self):
        """Инициализация с переменными окружения"""
        os.environ["RECEIPT_RECOGNIZER_API_URL"] = "https://test.com"
        os.environ["RECEIPT_RECOGNIZER_CLIENT_TOKEN"] = "test_token"

        from receipt_recognizer import ReceiptRecognizerClient
        client = ReceiptRecognizerClient()

        assert client.api_url == "https://test.com"
        assert client.client_token == "test_token"

        # Очищаем переменные окружения
        del os.environ["RECEIPT_RECOGNIZER_API_URL"]
        del os.environ["RECEIPT_RECOGNIZER_CLIENT_TOKEN"]

    def test_init_with_parameters(self):
        """Инициализация с явными параметрами"""
        os.environ["RECEIPT_RECOGNIZER_API_URL"] = "ignored"
        os.environ["RECEIPT_RECOGNIZER_CLIENT_TOKEN"] = "ignored"

        from receipt_recognizer import ReceiptRecognizerClient
        client = ReceiptRecognizerClient(
            api_url="https://explicit.com",
            client_token="explicit_token"
        )

        assert client.api_url == "https://explicit.com"
        assert client.client_token == "explicit_token"

        # Очищаем переменные окружения
        del os.environ["RECEIPT_RECOGNIZER_API_URL"]
        del os.environ["RECEIPT_RECOGNIZER_CLIENT_TOKEN"]

    @patch('requests.post')
    def test_recognize_success(self, mock_post):
        """Успешное распознавание чека"""
        # Настраиваем мок
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "source": "MIR ****1723",
                "destination": "****2853",
                "amount": 8700.00,
                "fee": 87.00,
                "date": "2020-03-31T11:44:30"
            }
        }
        mock_post.return_value = mock_response

        os.environ["RECEIPT_RECOGNIZER_API_URL"] = "https://test.com"
        os.environ["RECEIPT_RECOGNIZER_CLIENT_TOKEN"] = "test_token"

        from receipt_recognizer import ReceiptRecognizerClient
        client = ReceiptRecognizerClient()

        # Создаём временный файл для теста
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp.write(b'test image data')
            tmp_path = tmp.name

        try:
            result = client.recognize(tmp_path)
            assert result["amount"] == 8700.00
            assert result["source"] == "MIR ****1723"
        finally:
            import os
            os.unlink(tmp_path)

        # Проверяем заголовки запроса
        call_args = mock_post.call_args
        headers = call_args[1]['headers']
        assert headers['X-Client-Token'] == 'test_token'

        # Очищаем переменные окружения
        del os.environ["RECEIPT_RECOGNIZER_API_URL"]
        del os.environ["RECEIPT_RECOGNIZER_CLIENT_TOKEN"]