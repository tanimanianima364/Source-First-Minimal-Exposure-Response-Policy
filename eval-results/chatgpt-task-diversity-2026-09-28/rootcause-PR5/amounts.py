import re
from decimal import Decimal

_AMOUNT_PATTERN = re.compile(
    r"[+-]?(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)(?:\.[0-9]{1,2})?"
)


def parse_amount(text):
    if not isinstance(text, str):
        raise TypeError("amount must be a str")

    text = text.strip()

    if _AMOUNT_PATTERN.fullmatch(text) is None:
        raise ValueError(f"invalid amount: {text!r}")

    return Decimal(text.replace(",", ""))


def invoice_total(values):
    return sum((parse_amount(v) for v in values), Decimal(0))


def refund_amount(value):
    return -parse_amount(value)
