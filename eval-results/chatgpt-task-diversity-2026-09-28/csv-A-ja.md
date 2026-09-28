`Decimal`へ直接変換し、事前に文字列形式を検証すれば、二進浮動小数点を経由せず厳密に集計できます。

```python
import csv
import re
from decimal import Decimal
from pathlib import Path


_AMOUNT_RE = re.compile(r"[+-]?\d+(?:\.\d{1,2})?\Z")


def sum_csv(path: str | Path) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = {}

    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f, strict=True)

            try:
                header = next(reader)
            except StopIteration:
                raise ValueError("empty CSV file")

            if header != ["department", "amount"]:
                raise ValueError(
                    "header must be exactly: department,amount"
                )

            for line_no, row in enumerate(reader, start=2):
                if len(row) != 2:
                    raise ValueError(
                        f"line {line_no}: expected 2 columns, got {len(row)}"
                    )

                department, amount_text = row

                if department == "":
                    raise ValueError(
                        f"line {line_no}: department must not be empty"
                    )

                # Decimal() 自体は NaN / Infinity / 指数表記なども受け付けるため、
                # 要件どおりの十進表記か先に検証する。
                if _AMOUNT_RE.fullmatch(amount_text) is None:
                    raise ValueError(
                        f"line {line_no}: invalid amount: {amount_text!r}"
                    )

                amount = Decimal(amount_text)
                totals[department] = totals.get(
                    department, Decimal("0")
                ) + amount

    except csv.Error as e:
        raise ValueError(f"invalid CSV: {e}") from e

    return totals
```

動く最小の検証例です。

```python
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory


with TemporaryDirectory() as tmp:
    path = Path(tmp) / "data.csv"

    path.write_text(
        "department,amount\n"
        "sales,10.25\n"
        "engineering,+20\n"
        "sales,-3.10\n",
        encoding="utf-8",
    )

    assert sum_csv(path) == {
        "sales": Decimal("7.15"),
        "engineering": Decimal("20"),
    }

    # 不正な金額は無視せず ValueError
    path.write_text(
        "department,amount\n"
        "sales,NaN\n",
        encoding="utf-8",
    )

    try:
        sum_csv(path)
    except ValueError:
        pass
    else:
        raise AssertionError("ValueError was not raised")

print("OK")
```

この実装では `NaN`、`Infinity`、空欄、3桁以上の小数、指数表記、空の部署名、列数不一致、空ファイル、ヘッダー不一致をすべて `ValueError` とします。`float` は一度も使用しません。