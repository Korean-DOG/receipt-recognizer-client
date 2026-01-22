"""Тесты базовых констант"""
def test_base_fields():
    from receipt_recognizer.constants import *

    assert SOURCE == "source"
    assert DESTINATION == "destination"
    assert AMOUNT == "amount"
    assert FEE == "fee"
    assert DATE == "date"

    assert len(BASE_FIELDS) == 5
    assert "source" in BASE_FIELDS
    assert "amount" in BASE_FIELDS

    # Проверяем описания
    assert BASE_FIELDS_DESC[SOURCE] == "Source account/card (sender)"
    assert BASE_FIELDS_DESC[AMOUNT] == "Transaction amount in rubles"