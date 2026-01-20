"""Тесты базовых констант и утилит"""
from receipt_recognizer.constants import *

def test_base_fields():
    """Проверяем, что все базовые поля определены"""
    assert SOURCE == "source"
    assert DESTINATION == "destination"
    assert AMOUNT == "amount"
    assert FEE == "fee"
    assert DATE == "date"

def test_base_fields_list():
    """Проверяем список базовых полей"""
    assert len(BASE_FIELDS) == 5
    assert "source" in BASE_FIELDS
    assert "amount" in BASE_FIELDS

def test_field_descriptions():
    """Проверяем описания полей"""
    assert BASE_FIELDS_DESC[SOURCE] == "Source account/card (sender)"
    assert BASE_FIELDS_DESC[AMOUNT] == "Transaction amount in rubles"