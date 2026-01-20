"""
Base fields constants for receipt recognition.
These are standard fields that all receipts should support.
"""

# Base field constants
SOURCE = "source"           # Отправитель (sender)
DESTINATION = "destination"  # Получатель (recipient)
AMOUNT = "amount"           # Сумма операции
FEE = "fee"                # Комиссия
DATE = "date"              # Дата операции

# All base fields
BASE_FIELDS = [
    SOURCE,
    DESTINATION,
    AMOUNT,
    FEE,
    DATE,
]

# Field descriptions (for documentation)
BASE_FIELDS_DESC = {
    SOURCE: "Source account/card (sender)",
    DESTINATION: "Destination account/card (recipient)",
    AMOUNT: "Transaction amount in rubles",
    FEE: "Transaction fee/commission in rubles",
    DATE: "Transaction date and time",
}