共有原因は `parse_amount()` が入力契約を検証せず、そのまま `Decimal(text)` に渡していることです。カンマを正規化しつつ、`NaN` / `Infinity` や指数表記など `Decimal` が受理してしまう契約外入力も事前に排除します。

```python
import re
from decimal import Decimal

_AMOUNT_RE = re.compile(
    r"[+-]?(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)(?:\.[0-9]{1,2})?\Z"
)


def parse_amount(text):
    if not isinstance(text, str):
        raise TypeError("amount must be a str")

    text = text.strip()

    if not _AMOUNT_RE.fullmatch(text):
        raise ValueError(f"invalid amount: {text!r}")

    return Decimal(text.replace(",", ""))


def invoice_total(values):
    return sum((parse_amount(v) for v in values), Decimal(0))


def refund_amount(value):
    return -parse_amount(value)
```

`pytest` なら、両呼び出し元について正常系と不正入力を次のように確認できます。

```python
from decimal import Decimal

import pytest

# 実際には対象モジュールから import
# from your_module import invoice_total, refund_amount


def test_invoice_total_accepts_valid_amounts():
    assert invoice_total(["1,200.50", "-20.25"]) == Decimal("1180.25")
    assert invoice_total(["  +1,000  ", "20", "0.5"]) == Decimal("1020.5")


def test_refund_amount_accepts_valid_amount():
    assert refund_amount("1,200.50") == Decimal("-1200.50")
    assert refund_amount("  -20.25  ") == Decimal("20.25")


@pytest.mark.parametrize(
    "bad_value",
    [
        "1,20.50",       # 不正な3桁区切り
        "12,34,567",     # 不正な3桁区切り
        "1,234.567",     # 小数3桁
        "1.",            # 小数部なし
        ".50",           # 整数部なし
        "1e3",           # 指数表記
        "NaN",
        "+NaN",
        "Infinity",
        "-Infinity",
        "",
        "   ",
        "1 200",
        "1,234,",        # 末尾カンマ
    ],
)
def test_invoice_total_rejects_invalid_string(bad_value):
    with pytest.raises(ValueError):
        invoice_total([bad_value])


@pytest.mark.parametrize(
    "bad_value",
    [
        "1,20.50",
        "12,34,567",
        "1,234.567",
        "1.",
        ".50",
        "1e3",
        "NaN",
        "+NaN",
        "Infinity",
        "-Infinity",
        "",
        "   ",
        "1 200",
        "1,234,",
    ],
)
def test_refund_amount_rejects_invalid_string(bad_value):
    with pytest.raises(ValueError):
        refund_amount(bad_value)


@pytest.mark.parametrize("bad_value", [None, 1200, Decimal("1200"), 12.5])
def test_invoice_total_rejects_non_string(bad_value):
    with pytest.raises(TypeError):
        invoice_total([bad_value])


@pytest.mark.parametrize("bad_value", [None, 1200, Decimal("1200"), 12.5])
def test_refund_amount_rejects_non_string(bad_value):
    with pytest.raises(TypeError):
        refund_amount(bad_value)
```

この修正では `"1,200.50"` を検証後に `"1200.50"` へ正規化するため、質問の呼び出しは `Decimal("1180.25")` になります。同時に、`Decimal` 単体では受理され得る `NaN`、`Infinity`、`1e3` なども入力契約どおり `ValueError` に統一されます。