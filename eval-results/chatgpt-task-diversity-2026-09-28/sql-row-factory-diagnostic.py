"""Post-response diagnostic; not part of the preregistered checks."""
import sqlite3
import sys
import inventory as m

print("Python", sys.version.split()[0], "SQLite", sqlite3.sqlite_version)
conn = sqlite3.connect(":memory:")
try:
    conn.execute("CREATE TABLE users(id INTEGER, username TEXT UNIQUE, email TEXT)")
    conn.execute("INSERT INTO users VALUES(1, 'alice', 'alice@example.com')")
    for factory in (None, sqlite3.Row):
        conn.row_factory = factory
        result = m.get_user(conn, "alice")
        print("factory:", factory, "returned:", type(result).__name__)
        assert isinstance(result, tuple), "get_user must return tuple"
        assert result == (1, "alice", "alice@example.com")
        assert m.get_user(conn, "missing") is None
        assert conn.row_factory is factory and conn.in_transaction
finally:
    conn.close()
print("SQL row-factory diagnostic passed")
