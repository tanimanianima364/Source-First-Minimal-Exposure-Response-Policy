def p(d):
    result = []

    for item in d:
        a = item.get("a")

        if a and a > 0:
            result.append(a * 2)

    return result


def original(d):
    r = []
    for x in d:
        if x.get("a") and x["a"] > 0:
            r.append(x["a"] * 2)
    return r


def refactored(d):
    result = []

    for item in d:
        a = item.get("a")

        if a and a > 0:
            result.append(a * 2)

    return result


test_cases = [
    {},             # a が欠損
    {"a": None},    # None
    {"a": 0},       # 0
    {"a": -3},      # 負数
    {"a": 4},       # 正数
]

assert original(test_cases) == refactored(test_cases)

print(original(test_cases))
print(refactored(test_cases))


test_cases = {
    "missing": [{}],
    "None": [{"a": None}],
    "zero": [{"a": 0}],
    "negative": [{"a": -3}],
    "positive": [{"a": 4}],
}

for name, data in test_cases.items():
    expected = original(data)
    actual = refactored(data)

    assert actual == expected, (
        f"{name}: original={expected}, refactored={actual}"
    )

    print(f"{name:8}: {actual}")
