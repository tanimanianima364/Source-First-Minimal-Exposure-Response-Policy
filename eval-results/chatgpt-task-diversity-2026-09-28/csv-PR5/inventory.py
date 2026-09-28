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
