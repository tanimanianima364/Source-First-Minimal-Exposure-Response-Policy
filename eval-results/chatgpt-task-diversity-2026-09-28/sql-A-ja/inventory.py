import sqlite3


def get_user(conn: sqlite3.Connection, username: str):
    """
    username が完全一致するユーザーを tuple で返す。
    見つからない場合は None。

    conn の commit / close は行わない。
    """
    cursor = conn.execute(
        "SELECT id, username, email FROM users WHERE username = ?",
        (username,),
    )
    row = cursor.fetchone()
    return tuple(row) if row is not None else None


def test_get_user():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE users (
            id INTEGER,
            username TEXT UNIQUE,
            email TEXT
        )
        """
    )

    conn.execute(
        "INSERT INTO users VALUES (?, ?, ?)",
        (1, "alice", "alice@example.com"),
    )

    # SQLとして解釈されると危険な文字列そのものをユーザー名として登録する。
    malicious = "x' OR 1=1 --"
    conn.execute(
        "INSERT INTO users VALUES (?, ?, ?)",
        (2, malicious, "malicious@example.com"),
    )
    conn.commit()

    # 通常の完全一致
    assert get_user(conn, "alice") == (
        1,
        "alice",
        "alice@example.com",
    )

    # 存在しないユーザー
    assert get_user(conn, "bob") is None

    # 悪意ある文字列もSQLではなく単なる値として完全一致する
    assert get_user(conn, malicious) == (
        2,
        malicious,
        "malicious@example.com",
    )

    # インジェクション風文字列で他ユーザーを取得できない
    assert get_user(conn, "' OR 1=1 --") is None

    # get_user が commit していないことを確認する。
    conn.execute(
        "INSERT INTO users VALUES (?, ?, ?)",
        (3, "uncommitted", "pending@example.com"),
    )
    assert get_user(conn, "uncommitted") == (
        3,
        "uncommitted",
        "pending@example.com",
    )
    conn.rollback()

    # get_user が commit していれば、この行は残ってしまう。
    assert get_user(conn, "uncommitted") is None

    # 接続が閉じられていないことも確認
    assert conn.execute("SELECT COUNT(*) FROM users").fetchone() == (2,)

    conn.close()


if __name__ == "__main__":
    test_get_user()
    print("all tests passed")
