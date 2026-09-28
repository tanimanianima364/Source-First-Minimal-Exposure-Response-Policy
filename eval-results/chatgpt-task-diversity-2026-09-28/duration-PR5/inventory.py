import re

_DURATION_RE = re.compile(
    r"(?:(?P<h>[0-9]+)h)?"
    r"(?:(?P<m>[0-9]+)m)?"
    r"(?:(?P<s>[0-9]+)s)?"
)


def _ascii_int(digits):
    """ASCII数字列を、桁数制限に依存せずintへ変換する。"""
    value = 0
    for ch in digits:
        value = value * 10 + (ord(ch) - ord("0"))
    return value


def parse_duration(text):
    if not isinstance(text, str):
        raise TypeError("text must be str")

    match = _DURATION_RE.fullmatch(text)
    if match is None or not text:
        raise ValueError("invalid duration format")

    h, m, s = match.group("h", "m", "s")

    hours = _ascii_int(h) if h is not None else 0
    minutes = _ascii_int(m) if m is not None else 0
    seconds = _ascii_int(s) if s is not None else 0

    return hours * 3600 + minutes * 60 + seconds


# --- small executable tests ---

assert parse_duration("1h30m45s") == 5445
assert parse_duration("0s") == 0
assert parse_duration("2h") == 7200
assert parse_duration("3m5s") == 185
assert parse_duration("1h5s") == 3605


def assert_raises(exc_type, value):
    try:
        parse_duration(value)
    except exc_type:
        return
    except Exception as exc:
        raise AssertionError(
            f"expected {exc_type.__name__}, got {type(exc).__name__}"
        ) from exc
    raise AssertionError(f"expected {exc_type.__name__} for {value!r}")


# 書式不正
for invalid in (
    "",
    "1",
    "1h1h",
    "1s2m",
    "1m2h",
    " 1h",
    "1h ",
    "+1s",
    "-1s",
    "1.5s",
    "１s",       # ASCII数字ではない
    "1H",
    "1x",
):
    assert_raises(ValueError, invalid)

# 非str
for invalid in (None, 123, b"1s"):
    assert_raises(TypeError, invalid)

# 非常に大きな値も受理する
assert parse_duration("9" * 5000 + "s") > 0

print("all tests passed")
