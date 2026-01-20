
Receipt Recognizer Client Wrapper
Библиотека-обертка для работы с receipt-recognizer-client с поддержкой стандартизированных полей и опциональной Telegram-интеграцией.

Особенности
* 📸 Интеграция с Yandex Vision API через внешнюю библиотеку
* 🔄 Стандартизированные поля - единый формат для всех банков
* 🤖 Telegram-интеграция (опционально) - обработка чеков через бота
* 🛡️ Безопасность - хранение токенов в переменных окружения
* 🧩 Модульность - два варианта установки: базовый и с Telegram 

# Установка

## Вариант 1: Базовая установка (без Telegram)
```shell
# Через pip
pip install git+https://github.com/your-username/receipt-recognizer-client-wrapper.git

# Или через requirements.txt
echo "receipt-recognizer-client-wrapper @ git+https://github.com/your-username/receipt-recognizer-client-wrapper.git" >> requirements.txt
```
## Вариант 2: С Telegram-интеграцией
```shell
# Установка с дополнительными зависимостями
pip install "receipt-recognizer-client-wrapper[telegram] @ git+https://github.com/your-username/receipt-recognizer-client-wrapper.git"

# Или в requirements.txt:
# receipt-recognizer-client-wrapper[telegram] @ git+https://github.com/your-username/receipt-recognizer-client-wrapper.git
```
# Использование
## Базовая версия (без Telegram)
```python
import os
from receipt_recognizer import ReceiptRecognizerClient
from receipt_recognizer.constants import SOURCE, DESTINATION, AMOUNT, FEE, DATE

# Инициализация клиента
client = ReceiptRecognizerClient(
    api_key=os.getenv("YANDEX_VISION_API_KEY"),
    folder_id=os.getenv("YANDEX_FOLDER_ID")
)

# Распознавание чека
result = client.recognize("path/to/receipt.jpg")

# Доступ к стандартизированным полям
print(f"Отправитель: {result[SOURCE]}")
print(f"Получатель: {result[DESTINATION]}")
print(f"Сумма: {result[AMOUNT]:.2f} руб.")
print(f"Комиссия: {result.get(FEE, 0):.2f} руб.")
print(f"Дата: {result[DATE]}")

# Валидация полей
if client.validate_fields(result):
    print("Все обязательные поля присутствуют")
```
## Пример с обработкой нескольких файлов
```python
import os
from receipt_recognizer import ReceiptRecognizerClient

def process_receipts(folder_path):
    """Обработка всех чеков в папке"""
    client = ReceiptRecognizerClient()
    receipts_data = []

    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            try:
                filepath = os.path.join(folder_path, filename)
                result = client.recognize(filepath)

                # Добавляем только валидные чеки
                if client.validate_fields(result):
                    receipts_data.append({
                        'filename': filename,
                        'data': result
                    })
                    print(f"✓ {filename} - успешно распознан")
                else:
                    print(f"✗ {filename} - отсутствуют обязательные поля")

            except Exception as e:
                print(f"✗ {filename} - ошибка: {str(e)}")

    return receipts_data

# Использование
receipts = process_receipts("receipts/")
```
# Telegram версия
```python
import os
from receipt_recognizer.telegram_integration import create_telegram_client

# Создание Telegram-бота
bot = create_telegram_client(
    token=os.getenv("TELEGRAM_BOT_TOKEN"),
    api_key=os.getenv("YANDEX_VISION_API_KEY"),
    folder_id=os.getenv("YANDEX_FOLDER_ID"),
    target_chat_id=os.getenv("TELEGRAM_TARGET_CHAT_ID")  # Опционально
)

# Запуск бота
if __name__ == "__main__":
    bot.start()
```
## Интеграция в существующий проект
**В requirements.txt вашего проекта:**
```shell
# Для базовой версии
receipt-recognizer-client-wrapper @ git+https://github.com/Korean-DOG/receipt-recognizer-client-wrapper.git
# Для версии с Telegram
receipt-recognizer-client-wrapper[telegram] @ git+https://github.com/Korean-DOG/receipt-recognizer-client-wrapper.git
```
**Пример FastAPI приложения**
```python
from fastapi import FastAPI, UploadFile, File
from receipt_recognizer import ReceiptRecognizerClient
import os

app = FastAPI()
client = ReceiptRecognizerClient()

@app.post("/recognize/")
async def recognize_receipt(file: UploadFile = File(...)):
    """API endpoint для распознавания чеков"""
    
    # Сохраняем временный файл
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(await file.read())
    
    try:
        # Распознаем чек
        result = client.recognize(temp_path)
        
        # Удаляем временный файл
        os.remove(temp_path)
        
        return {
            "success": True,
            "data": result,
            "filename": file.filename
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "filename": file.filename
        }
```
# Базовые поля
## Библиотека гарантирует наличие следующих полей:

|Поле|Описание| Пример                |
|-------------|--------------|-----------------------|
|source|Отправитель (карта/счет)| "MIR ****1723"        |
|destination|Получатель (карта/счет)| "****2853"            |
|amount|Сумма операции (руб.)| 8700.00               |
|fee|Комиссия (руб.)| 87.00                 |
|date|Дата и время операции| "2020-03-31T11:44:30" |

# Логирование и отладка
```python
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# В вашем коде
try:
    result = client.recognize("receipt.jpg")
    logger.info(f"Чек распознан: {result['amount']} руб.")
except Exception as e:
    logger.error(f"Ошибка распознавания: {str(e)}")
```
# Обработка ошибок
```python
from receipt_recognizer import ReceiptRecognizerClient

client = ReceiptRecognizerClient()

try:
    result = client.recognize("receipt.jpg")
    
    # Проверка наличия обязательных полей
    if not client.validate_fields(result):
        print("Предупреждение: не все поля заполнены")
    
    # Использование данных
    if result.get("amount"):
        process_payment(result["amount"])
        
except FileNotFoundError:
    print("Файл не найден")
except ValueError as e:
    print(f"Ошибка валидации: {str(e)}")
except Exception as e:
    print(f"Неизвестная ошибка: {str(e)}")
```
# Тестирование
```python
# tests/test_receipt_recognizer.py
import pytest
from receipt_recognizer import ReceiptRecognizerClient

def test_recognize_receipt():
    """Тест распознавания чека"""
    client = ReceiptRecognizerClient()
    
    # Используем тестовый файл
    result = client.recognize("tests/test_receipt.jpg")
    
    assert "amount" in result
    assert result["amount"] > 0
    assert client.validate_fields(result)
```
# Поддерживаемые форматы
* Изображения: JPG, PNG, BMP, WebP
* Документы: **PDF**

# Банки
* Сбербанк
* Тинькофф

## 🔄 Совместимость версий

### Что делать, если клиентская библиотека несовместима с сервером?

Если вы получаете ошибку совместимости, следуйте этим шагам:

#### 1. **Проверьте версии**
```bash
python -c "import receipt_recognizer; print(f'Client version: {receipt_recognizer.__version__}')"
```
#### 2. Если клиент устарел:
```bash
# Обновите клиентскую библиотеку
pip install --upgrade receipt-recognizer-client-wrapper

# Или установите конкретную версию
pip install receipt-recognizer-client-wrapper==1.2.0
```
3. Если сервер обновился:
1. [ ] Свяжитесь с администратором сервера для получения информации:
2. [ ] Какая версия сервера сейчас работает
3. [ ] Какая версия клиента совместима
4. [ ] Есть ли миграционный путь

## 🤖 Telegram Integration

### Вариант 1: Интеграция в существующего бота (рекомендуется)

```python
from telegram.ext import Application
from receipt_recognizer import ReceiptRecognizerClient
from receipt_recognizer.telegram_integration import setup_receipt_handlers

# Создайте или получите существующий Application
application = Application.builder().token("YOUR_BOT_TOKEN").build()

# Создайте клиент для распознавания
recognizer = ReceiptRecognizerClient(
    api_url="https://your-api.com",
    client_token="your_client_token"
)

# Настройте конфигурацию (опционально)
config = {
    "target_chat_id": "-123456789",  # Чат для пересылки
}

# Добавьте обработчики чеков в вашего бота
setup_receipt_handlers(application, recognizer, config)

# Запустите бота как обычно
application.run_polling()
