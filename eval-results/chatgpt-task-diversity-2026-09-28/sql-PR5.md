## 結論

`?` プレースホルダによるパラメータ化クエリを使えば、完全一致を維持しつつSQLインジェクションを防げます。`get_user` は `commit()` / `close()` を呼びません。

```python
import sqlite3


def get_user(conn, username):
    cursor = conn.execute(
        "SELECT id, username, email FROM users WHERE username = ?",
        (username,),
    )
    return cursor.fetchone()


def test_get_user():
    conn = sqlite3.connect(":memory:")

    conn.execute("""
        CREATE TABLE users (
            id INTEGER,
            username TEXT UNIQUE,
            email TEXT
        )
    """)

    conn.executemany(
        "INSERT INTO users (id, username, email) VALUES (?, ?, ?)",
        [
            (1, "alice", "alice@example.com"),
            (2, "o'reilly", "oreilly@example.com"),
        ],
    )

    # 完全一致
    assert get_user(conn, "alice") == (
        1,
        "alice",
        "alice@example.com",
    )
    assert get_user(conn, "ali") is None

    # クォートを含む正当なユーザー名
    assert get_user(conn, "o'reilly") == (
        2,
        "o'reilly",
        "oreilly@example.com",
    )

    # 典型的なSQLインジェクション文字列でも一致しない
    assert get_user(conn, "' OR 1=1 --") is None

    # 複数文・DROP TABLEを狙う入力も単なる文字列として扱われる
    malicious = "alice'; DROP TABLE users; --"
    assert get_user(conn, malicious) is None

    # テーブルが破壊されていないことを確認
    assert conn.execute(
        "SELECT COUNT(*) FROM users"
    ).fetchone() == (2,)

    # get_user() が暗黙にcommitしていないことを確認
    assert conn.in_transaction

    # get_user() が接続を閉じていないことを確認
    assert conn.execute("SELECT 1").fetchone() == (1,)

    # テスト自身が所有する接続なので、最後にテスト側で閉じる
    conn.close()


if __name__ == "__main__":
    test_get_user()
    print("All tests passed.")
```

## Missing piece

重要なのは、`username` をSQL文字列へ連結・補間しないことです。`WHERE username = ?` と `(username,)` を分離して渡すため、`' OR 1=1 --` などもSQL構文ではなく単なる値としてSQLiteに渡されます。

## Next directions

必要なら、同じ実装を `pytest` のテスト形式、型ヒント付き、または `sqlite3.Row` 使用版に変換できます。