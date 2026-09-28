```python
import re

_DURATION_RE = re.compile(
    r"(?:(?P<h>[0-9]+)h)?"
    r"(?:(?P<m>[0-9]+)m)?"
    r"(?:(?P<s>[0-9]+)s)?"
)


def _parse_uint_ascii(digits: str) -> int:
    """ASCII 10進整数を、桁数上限に依存せず int に変換する。"""
    value = 0
    for i in range(0, len(digits), 9):
        chunk = digits[i:i + 9]
        value = value * (10 ** len(chunk)) + int(chunk)
    return value


def parse_duration(text: str) -> int:
    if not isinstance(text, str):
        raise TypeError("text must be str")

    match = _DURATION_RE.fullmatch(text)
    if match is None or all(
        match.group(unit) is None for unit in ("h", "m", "s")
    ):
        raise ValueError("invalid duration format")

    h = (
        _parse_uint_ascii(match.group("h"))
        if match.group("h") is not None
        else 0
    )
    m = (
        _parse_uint_ascii(match.group("m"))
        if match.group("m") is not None
        else 0
    )
    s = (
        _parse_uint_ascii(match.group("s"))
        if match.group("s") is not None
        else 0
    )

    return h * 3600 + m * 60 + s


# ---- small executable tests ----

assert parse_duration("1h30m45s") == 5445
assert parse_duration("0s") == 0
assert parse_duration("2h") == 7200
assert parse_duration("15m") == 900
assert parse_duration("1h5s") == 3605
assert parse_duration("00h00m00s") == 0

# 非常に大きい整数も受け付ける
assert parse_duration("1" + "0" * 5000 + "s") == 10 ** 5000

invalid_strings = [
    "",
    "1",
    "1m2h",       # 順序違反
    "1h2h",       # 同じ単位が複数回
    "1.5h",
    "+1h",
    "-1s",
    " 1h",
    "1h ",
    "1 h",
    "１h",        # 全角数字
    "1H",
    "1hX",
]

for value in invalid_strings:
    try:
        parse_duration(value)
    except ValueError:
        pass
    else:
        raise AssertionError(f"ValueError expected: {value!r}")

for value in [None, 1, 1.0, b"1h", []]:
    try:
        parse_duration(value)
    except TypeError:
        pass
    else:
        raise AssertionError(f"TypeError expected: {value!r}")

print("all tests passed")
```

`[0-9]`を使っているためUnicode数字は受理しません。また、Pythonの環境によって存在する巨大な10進文字列に対する`int()`の桁数制限を避けるため、9桁ずつ変換しています。