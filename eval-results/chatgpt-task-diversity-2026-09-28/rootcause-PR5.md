共有原因は `parse_amount()` が入力契約を検証せず、そのまま `Decimal(text)` に渡している点です。`Decimal` はカンマ区切りを受け付けない一方、`NaN`・`Infinity`・指数表記など、今回禁止したい形式の一部は受け付けます。そのため、**共有の `parse_amount()` で型・書式を検証してからカンマを除去**するのが適切です。

### 修正版コード全体

```python
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
```

これで例えば、

```python
invoice_total(["1,200.50", "-20.25"])
# Decimal('1180.25')

refund_amount("1,200.50")
# Decimal('-1200.50')
```

となります。

### pytest テスト

```python
from decimal import Decimal

import pytest

from amounts import invoice_total, refund_amount


# ---- invoice_total: 正常入力 ----

@pytest.mark.parametrize(
    ("values", "expected"),
    [
        (["1,200.50", "-20.25"], Decimal("1180.25")),
        (["100", "20.5", "+3.25"], Decimal("123.75")),
        (["  1,000  ", "  -5.50 "], Decimal("994.50")),
        ([], Decimal("0")),
    ],
)
def test_invoice_total_valid(values, expected):
    assert invoice_total(values) == expected


# ---- invoice_total: 不正入力 ----

@pytest.mark.parametrize(
    "value",
    [
        "1,20.50",       # 不正な3桁区切り
        "12,34,567",     # 不正な3桁区切り
        "1,200.123",     # 小数3桁
        "1.",            # 小数点の後に数字なし
        ".50",           # 整数部なし
        "1e3",           # 指数表記
        "NaN",
        "Infinity",
        "-Infinity",
        "",
        "   ",
        "+",
        "1 200",
    ],
)
def test_invoice_total_invalid_value(value):
    with pytest.raises(ValueError):
        invoice_total([value])


@pytest.mark.parametrize("value", [1200, Decimal("1200"), None, b"1200"])
def test_invoice_total_non_string(value):
    with pytest.raises(TypeError):
        invoice_total([value])


# ---- refund_amount: 正常入力 ----

@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1,200.50", Decimal("-1200.50")),
        ("-20.25", Decimal("20.25")),
        ("+100", Decimal("-100")),
        ("  1,000.5  ", Decimal("-1000.5")),
    ],
)
def test_refund_amount_valid(value, expected):
    assert refund_amount(value) == expected


# ---- refund_amount: 不正入力 ----

@pytest.mark.parametrize(
    "value",
    [
        "1,20.50",
        "12,34,567",
        "1,200.123",
        "1.",
        ".50",
        "1e3",
        "NaN",
        "Infinity",
        "-Infinity",
        "",
        "   ",
        "+",
        "1 200",
    ],
)
def test_refund_amount_invalid_value(value):
    with pytest.raises(ValueError):
        refund_amount(value)


@pytest.mark.parametrize("value", [1200, Decimal("1200"), None, b"1200"])
def test_refund_amount_non_string(value):
    with pytest.raises(TypeError):
        refund_amount(value)
```

重要なのは `Decimal` 自体をバリデータとして使わないことです。正規表現で契約を限定しているため、`"1200"` と `"1,200"` は許可されますが、`"12,00"`、`"1e3"`、`"NaN"` などは一貫して `ValueError` になります。