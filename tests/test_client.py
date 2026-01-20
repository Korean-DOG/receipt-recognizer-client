"""Тесты основного клиента"""
import pytest
from unittest.mock import Mock, patch
from receipt_recognizer import ReceiptRecognizerClient
from receipt_recognizer.exceptions import APIError, ValidationError


class TestReceiptRecognizerClient:
    def test_init_without_token(self):
        """Инициализация без токена должна вызывать ошибку"""
        with pytest.raises(ValueError, match="CLIENT_TOKEN is required"):
            ReceiptRecognizerClient(api_url="https://test.com")

    def test_init_with_env_token(self, mock_env):
        """Инициализация с токеном из переменных окружения"""
        client = ReceiptRecognizerClient(api_url="https://test.com")
        assert client.api_url == "https://test.com"
        assert client.client_token == "test_token_123"

    def test_init_with_explicit_token(self):
        """Инициализация с явно указанным токеном"""
        client = ReceiptRecognizerClient(
            api_url="https://test.com",
            client_token="explicit_token"
        )
        assert client.client_token == "explicit_token"

    @patch('receipt_recognizer.client.requests.post')
    def test_recognize_success(self, mock_post, mock_response):
        """Успешное распознавание чека"""
        # Настраиваем мок
        mock_response_obj = Mock()
        mock_response_obj.status_code = 200
        mock_response_obj.json.return_value = {
            "success": True,
            "data": mock_response
        }
        mock_post.return_value = mock_response_obj

        # Создаем клиент и вызываем метод
        client = ReceiptRecognizerClient(
            api_url="https://test.com",
            client_token="test_token"
        )

        result = client.recognize("test.jpg")

        # Проверяем вызов API
        mock_post.assert_called_once()
        call_args = mock_post.call_args

        # Проверяем заголовки
        headers = call_args[1]['headers']
        assert headers['X-Client-Token'] == 'test_token'
        assert headers['Content-Type'] == 'application/json'

        # Проверяем результат
        assert result['amount'] == 8700.00
        assert result['source'] == "MIR ****1723"

    @patch('receipt_recognizer.client.requests.post')
    def test_recognize_api_error(self, mock_post):
        """Ошибка API при распознавании"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "Invalid token"}
        mock_post.return_value = mock_response

        client = ReceiptRecognizerClient(
            api_url="https://test.com",
            client_token="invalid_token"
        )

        with pytest.raises(APIError, match="Invalid token"):
            client.recognize("test.jpg")

    @patch('receipt_recognizer.client.requests.post')
    def test_recognize_network_error(self, mock_post):
        """Сетевая ошибка"""
        mock_post.side_effect = ConnectionError("Network error")

        client = ReceiptRecognizerClient(
            api_url="https://test.com",
            client_token="test_token"
        )

        with pytest.raises(APIError, match="Network error"):
            client.recognize("test.jpg")

    def test_validate_result_valid(self, mock_response):
        """Валидация правильного результата"""
        client = ReceiptRecognizerClient(
            api_url="https://test.com",
            client_token="test_token"
        )

        # Должно пройти без ошибок
        client._validate_result(mock_response)

    def test_validate_result_missing_field(self):
        """Валидация результата с отсутствующим полем"""
        client = ReceiptRecognizerClient(
            api_url="https://test.com",
            client_token="test_token"
        )

        invalid_result = {
            "source": "MIR ****1723",
            "destination": "****2853",
            # amount отсутствует
            "fee": 87.00,
            "date": "2020-03-31T11:44:30"
        }

        with pytest.raises(ValidationError, match="Missing required field: amount"):
            client._validate_result(invalid_result)