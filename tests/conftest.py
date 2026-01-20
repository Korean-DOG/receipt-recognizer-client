import os
import sys
from pathlib import Path
from unittest.mock import patch

# Добавляем корень проекта в PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
from dotenv import load_dotenv

# Загружаем тестовые переменные окружения
test_env = project_root / ".env.test"
if test_env.exists():
    load_dotenv(test_env)

@pytest.fixture
def mock_env():
    """Мок переменных окружения"""
    with patch.dict(os.environ, {
        'RECEIPT_RECOGNIZER_API_URL': 'https://api.test.com',
        'CLIENT_TOKEN': 'test_token_123',
    }):
        yield

@pytest.fixture
def sample_image_path():
    """Путь к тестовому изображению"""
    return Path(__file__).parent / "fixtures" / "sample_receipt.jpg"

@pytest.fixture
def mock_response():
    """Мок успешного ответа от API"""
    return {
        "source": "MIR ****1723",
        "destination": "****2853",
        "amount": 8700.00,
        "fee": 87.00,
        "date": "2020-03-31T11:44:30",
        "bank": "Сбербанк",
        "status": "УСПЕШНО"
    }