def p(d):
    result = []

    for x in d:
        a = x.get("a")
        if a is not None and a > 0:
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

    for x in d:
        a = x.get("a")
        if a is not None and a > 0:
            result.append(a * 2)

    return result


cases = [
    ("欠損", {}),
    ("None", {"a": None}),
    ("0", {"a": 0}),
    ("負数", {"a": -3}),
    ("正数", {"a": 3}),
]

for name, item in cases:
    old_result = original([item])
    new_result = refactored([item])

    print(f"{name}: original={old_result}, refactored={new_result}")
    assert old_result == new_result

print("すべて同じ結果です")
