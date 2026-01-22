"""
Receipt Recognizer Client
"""

from .client import ReceiptRecognizerClient
from .constants import (
    BASE_FIELDS,
    SOURCE,
    DESTINATION,
    AMOUNT,
    FEE,
    DATE,
    BASE_FIELDS_DESC,
)
from .version import __version__, check_compatibility

__all__ = [
    "ReceiptRecognizerClient",
    "BASE_FIELDS",
    "SOURCE",
    "DESTINATION",
    "AMOUNT",
    "FEE",
    "DATE",
    "BASE_FIELDS_DESC",
    "__version__",
    "check_compatibility",
]