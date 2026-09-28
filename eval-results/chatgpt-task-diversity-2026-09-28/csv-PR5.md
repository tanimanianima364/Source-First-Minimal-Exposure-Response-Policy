## 結論

`Decimal`へ直接変換し、正規表現で固定小数点表記と小数桁数を先に検証すれば、二進浮動小数点を一切経由せず要件を満たせます。

```python
import csv
import re
from decimal import Decimal


_AMOUNT_RE = re.compile(r"[+-]?\d+(?:\.\d{1,2})?\Z")


def sum_csv(path: str) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = {}

    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f, strict=True)

            try:
                header = next(reader)
            except StopIteration:
                raise ValueError("empty CSV file") from None

            if header != ["department", "amount"]:
                raise ValueError(f"invalid header: {header!r}")

            for row in reader:
                line = reader.line_num

                if len(row) != 2:
                    raise ValueError(
                        f"line {line}: expected 2 columns, got {len(row)}"
                    )

                department, amount_text = row

                if department == "":
                    raise ValueError(f"line {line}: empty department")

                if not _AMOUNT_RE.fullmatch(amount_text):
                    raise ValueError(
                        f"line {line}: invalid amount: {amount_text!r}"
                    )

                amount = Decimal(amount_text)

                # 正規表現上は NaN/Infinity は通らないが、防御的に確認する。
                if not amount.is_finite():
                    raise ValueError(
                        f"line {line}: non-finite amount: {amount_text!r}"
                    )

                totals[department] = totals.get(department, Decimal("0")) + amount

    except (UnicodeDecodeError, csv.Error) as exc:
        raise ValueError(f"invalid CSV: {exc}") from exc

    return totals
```

最小の検証例です。

```python
import tempfile
from decimal import Decimal


with tempfile.NamedTemporaryFile(
    mode="w",
    encoding="utf-8",
    newline="",
    delete=False,
) as f:
    f.write(
        "department,amount\n"
        "Sales,10.10\n"
        "Engineering,-2.05\n"
        "Sales,+0.20\n"
    )
    path = f.name

assert sum_csv(path) == {
    "Sales": Decimal("10.30"),
    "Engineering": Decimal("-2.05"),
}


# 不正な金額は無視されず ValueError
with tempfile.NamedTemporaryFile(
    mode="w",
    encoding="utf-8",
    newline="",
    delete=False,
) as f:
    f.write("department,amount\nSales,NaN\n")
    bad_path = f.name

try:
    sum_csv(bad_path)
except ValueError:
    pass
else:
    raise AssertionError("ValueError was not raised")

print("OK")
```

### 補足

`[+-]?\d+(?:\.\d{1,2})?` としているため、`10`、`-10`、`+10.25` は有効で、空欄、`NaN`、`Infinity`、`1.234`、`1e3` は不正になります。`department` は「空文字だけを不正」と解釈しているため、`"   "` は非空文字列として有効です。

### 次の方向

- `unittest`だけで正常系・各異常系を網羅するテストを追加する。
- `"   "` のような空白だけの部署名も不正にするなら、`department.strip() == ""` に変更する。