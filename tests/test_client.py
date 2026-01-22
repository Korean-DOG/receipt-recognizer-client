"""Тесты основного клиента"""
import os
import tempfile
import pytest
from unittest.mock import Mock, patch
from receipt_recognizer import ReceiptRecognizerClient


def cleanup_env():
    """Очистка переменных окружения"""
    for var in ["RECEIPT_RECOGNIZER_API_URL", "RECEIPT_RECOGNIZER_CLIENT_TOKEN"]:
        if var in os.environ:
            del os.environ[var]


def test_init_without_env_vars():
    """Инициализация без переменных окружения должна вызывать ошибку"""
    cleanup_env()

    with pytest.raises(ValueError, match="API URL is required"):
        ReceiptRecognizerClient()


def test_init_with_env_vars():
    """Инициализация с переменными окружения"""
    cleanup_env()
    os.environ["RECEIPT_RECOGNIZER_API_URL"] = "https://test.com"
    os.environ["RECEIPT_RECOGNIZER_CLIENT_TOKEN"] = "test_token"

    client = ReceiptRecognizerClient()

    assert client.api_url == "https://test.com"
    assert client.client_token == "test_token"
    cleanup_env()


def test_init_with_parameters():
    """Инициализация с явными параметрами"""
    cleanup_env()

    client = ReceiptRecognizerClient(
        api_url="https://explicit.com",
        client_token="explicit_token"
    )

    assert client.api_url == "https://explicit.com"
    assert client.client_token == "explicit_token"
    cleanup_env()


def test_init_prefers_parameters_over_env():
    """Параметры должны иметь приоритет над переменными окружения"""
    cleanup_env()
    os.environ["RECEIPT_RECOGNIZER_API_URL"] = "https://env.com"
    os.environ["RECEIPT_RECOGNIZER_CLIENT_TOKEN"] = "env_token"

    client = ReceiptRecognizerClient(
        api_url="https://param.com",
        client_token="param_token"
    )

    assert client.api_url == "https://param.com"
    assert client.client_token == "param_token"
    cleanup_env()


@patch('requests.post')
def test_recognize_success(mock_post):
    """Успешное распознавание чека"""
    cleanup_env()
    os.environ["RECEIPT_RECOGNIZER_API_URL"] = "https://test.com"
    os.environ["RECEIPT_RECOGNIZER_CLIENT_TOKEN"] = "test_token"

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

    client = ReceiptRecognizerClient()

    # Создаём временный файл для теста
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False, delete_on_close=False) as tmp:
        tmp.write(b'test image data')
        tmp_path = tmp.name

    try:
        result = client.recognize(tmp_path)
        assert result["amount"] == 8700.00
        assert result["source"] == "MIR ****1723"

        # Проверяем заголовки запроса
        call_args = mock_post.call_args
        headers = call_args[1]['headers']
        assert headers['X-Client-Token'] == 'test_token'
    finally:
        os.unlink(tmp_path)

    cleanup_env()


@patch('requests.post')
def test_recognize_api_error(mock_post):
    """Ошибка API при распознавании"""
    cleanup_env()
    os.environ["RECEIPT_RECOGNIZER_API_URL"] = "https://test.com"
    os.environ["RECEIPT_RECOGNIZER_CLIENT_TOKEN"] = "test_token"

    mock_response = Mock()
    mock_response.status_code = 401
    mock_response.json.return_value = {"error": "Invalid token"}
    mock_post.return_value = mock_response

    client = ReceiptRecognizerClient()

    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False, delete_on_close=False) as tmp:
        tmp.write(b'test image data')
        tmp_path = tmp.name

    try:
        with pytest.raises(Exception, match="Invalid token"):
            client.recognize(tmp_path)
    finally:
        os.unlink(tmp_path)

    cleanup_env()


def test_validate_result():
    """Тест валидации результата"""
    cleanup_env()
    os.environ["RECEIPT_RECOGNIZER_API_URL"] = "https://test.com"
    os.environ["RECEIPT_RECOGNIZER_CLIENT_TOKEN"] = "test_token"

    client = ReceiptRecognizerClient()

    # Корректный результат
    valid_result = {
        "source": "test",
        "destination": "test",
        "amount": 100.0,
        "fee": 10.0,
        "date": "2024-01-01"
    }

    # Должен пройти без ошибок
    client._validate_result(valid_result)

    # Невалидный результат (отсутствует поле)
    invalid_result = {
        "source": "test",
        "destination": "test",
        # amount отсутствует
        "fee": 10.0,
        "date": "2024-01-01"
    }

    with pytest.raises(ValueError, match="Missing required fields: amount"):
        client._validate_result(invalid_result)

    cleanup_env()