from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable
from typing import Any

_MAX_LEN = 128
_MAX_QTY = 1_000_000_000
_BUSY_TIMEOUT_MS = 5_000

_RESERVE_KEYS = {"request_id", "op", "reservation_id", "sku", "qty"}
_TERMINAL_KEYS = {"request_id", "op", "reservation_id"}


def _connect(path) -> sqlite3.Connection:
    conn = sqlite3.connect(
        path,
        timeout=_BUSY_TIMEOUT_MS / 1000,
        isolation_level=None,
    )
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(f"PRAGMA busy_timeout = {_BUSY_TIMEOUT_MS}")
        return conn
    except BaseException:
        conn.close()
        raise


def _key(value: str) -> bytes:
    # sqlite3 の TEXT バインドは孤立サロゲートを拒否する。
    # 公開APIで許容している任意の Python str を保持できるよう、
    # 識別子は surrogatepass UTF-8 の BLOB として保存する。
    return str.encode(value, "utf-8", "surrogatepass")


def _from_key(value: bytes) -> str:
    return bytes.decode(value, "utf-8", "surrogatepass")


def _valid_id(value: Any) -> bool:
    return isinstance(value, str) and 1 <= len(value) <= _MAX_LEN


def _valid_int(value: Any, *, minimum: int) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and minimum <= value <= _MAX_QTY
    )


def _validate_stocks(stocks: Any) -> list[tuple[str, int]]:
    if not isinstance(stocks, dict) or not stocks:
        raise ValueError("stocks must be a non-empty dict")

    rows: list[tuple[str, int]] = []
    for sku, qty in stocks.items():
        if not _valid_id(sku):
            raise ValueError("each SKU must be a str of length 1..128")
        if not _valid_int(qty, minimum=0):
            raise ValueError(
                "each stock count must be an int in 0..10^9 "
                "(bool is invalid)"
            )
        rows.append((sku, qty))
    return rows


def _validate_command(command: Any) -> dict[str, Any]:
    if not isinstance(command, dict):
        raise ValueError("each command must be a dict")

    op = command.get("op")
    if not isinstance(op, str) or op not in {"reserve", "cancel", "ship"}:
        raise ValueError("invalid op")

    expected = _RESERVE_KEYS if op == "reserve" else _TERMINAL_KEYS
    if set(command) != expected:
        raise ValueError("command has missing or unexpected keys")

    request_id = command["request_id"]
    reservation_id = command["reservation_id"]

    if not _valid_id(request_id):
        raise ValueError(
            "request_id must be a str of length 1..128"
        )
    if not _valid_id(reservation_id):
        raise ValueError(
            "reservation_id must be a str of length 1..128"
        )

    if op == "reserve":
        sku = command["sku"]
        qty = command["qty"]

        if not _valid_id(sku):
            raise ValueError("sku must be a str of length 1..128")
        if not _valid_int(qty, minimum=1):
            raise ValueError(
                "qty must be an int in 1..10^9 "
                "(bool is invalid)"
            )

        return {
            "request_id": request_id,
            "op": op,
            "reservation_id": reservation_id,
            "sku": sku,
            "qty": qty,
        }

    return {
        "request_id": request_id,
        "op": op,
        "reservation_id": reservation_id,
    }


def _canonical_command(command: dict[str, Any]) -> str:
    return json.dumps(
        command,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def init_db(path, stocks) -> None:
    rows = _validate_stocks(stocks)

    conn = _connect(path)
    try:
        conn.execute("BEGIN IMMEDIATE")

        conn.execute(
            """
            CREATE TABLE stock (
                sku BLOB PRIMARY KEY,
                total INTEGER NOT NULL
                    CHECK (
                        typeof(total) = 'integer'
                        AND total BETWEEN 0 AND 1000000000
                    ),
                available INTEGER NOT NULL
                    CHECK (
                        typeof(available) = 'integer'
                        AND available BETWEEN 0 AND total
                    )
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE reservations (
                reservation_id BLOB PRIMARY KEY,
                sku BLOB NOT NULL,
                qty INTEGER NOT NULL
                    CHECK (
                        typeof(qty) = 'integer'
                        AND qty BETWEEN 1 AND 1000000000
                    ),
                state TEXT NOT NULL
                    CHECK (
                        state IN (
                            'RESERVED',
                            'CANCELLED',
                            'SHIPPED'
                        )
                    ),
                FOREIGN KEY (sku) REFERENCES stock(sku)
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE request_log (
                request_id BLOB PRIMARY KEY,
                command TEXT NOT NULL,
                status TEXT NOT NULL
                    CHECK (
                        status IN (
                            'RESERVED',
                            'CANCELLED',
                            'SHIPPED',
                            'OUT_OF_STOCK',
                            'NOT_FOUND',
                            'CONFLICT'
                        )
                    )
            )
            """
        )

        conn.executemany(
            """
            INSERT INTO stock(sku, total, available)
            VALUES (?, ?, ?)
            """,
            (
                (_key(sku), qty, qty)
                for sku, qty in rows
            ),
        )

        conn.commit()

    except BaseException:
        if conn.in_transaction:
            try:
                conn.rollback()
            except sqlite3.Error:
                pass
        raise

    finally:
        conn.close()


def apply_batch(
    path,
    commands,
    *,
    before_commit: Callable[[], Any] | None = None,
) -> list[dict]:
    if not isinstance(commands, list) or not commands:
        raise ValueError("commands must be a non-empty list")

    # 構文・型検査はDBの再送判定より前に全要素へ行う。
    # 値をコピーするため、以降は呼出し側dictのキー順等にも依存しない。
    normalized = [
        _validate_command(command)
        for command in commands
    ]

    conn = _connect(path)
    try:
        # SQLite自身の書込みロックをbatch全体に保持する。
        # 同一DBに対する独立プロセスのwrite batchもここで直列化される。
        conn.execute("BEGIN IMMEDIATE")

        results: list[dict] = []

        for command in normalized:
            request_id = command["request_id"]
            request_key = _key(request_id)

            op = command["op"]

            reservation_id = command["reservation_id"]
            reservation_key = _key(reservation_id)

            # 未登録SKU検査は request_id 再送判定より先。
            if op == "reserve":
                sku = command["sku"]
                sku_key = _key(sku)

                row = conn.execute(
                    "SELECT 1 FROM stock WHERE sku = ?",
                    (sku_key,),
                ).fetchone()

                if row is None:
                    raise ValueError(
                        f"unknown SKU: {sku!r}"
                    )

            canonical = _canonical_command(command)

            prior = conn.execute(
                """
                SELECT command, status
                FROM request_log
                WHERE request_id = ?
                """,
                (request_key,),
            ).fetchone()

            if prior is not None:
                prior_command, prior_status = prior

                if prior_command != canonical:
                    raise ValueError(
                        f"request_id {request_id!r} "
                        "was already used for different content"
                    )

                # 現在の在庫・予約状態は見ず、最初にコミットした結果を返す。
                results.append(
                    {
                        "request_id": request_id,
                        "status": prior_status,
                    }
                )
                continue

            if op == "reserve":
                sku = command["sku"]
                sku_key = _key(sku)
                qty = command["qty"]

                # 予約ID衝突を在庫不足判定より優先。
                existing = conn.execute(
                    """
                    SELECT 1
                    FROM reservations
                    WHERE reservation_id = ?
                    """,
                    (reservation_key,),
                ).fetchone()

                if existing is not None:
                    status = "CONFLICT"

                else:
                    # 条件付きUPDATEなので、DBレベルでも
                    # availableを負数にできない。
                    updated = conn.execute(
                        """
                        UPDATE stock
                           SET available = available - ?
                         WHERE sku = ?
                           AND available >= ?
                        """,
                        (qty, sku_key, qty),
                    )

                    if updated.rowcount == 0:
                        status = "OUT_OF_STOCK"

                    else:
                        conn.execute(
                            """
                            INSERT INTO reservations(
                                reservation_id,
                                sku,
                                qty,
                                state
                            )
                            VALUES (?, ?, ?, 'RESERVED')
                            """,
                            (
                                reservation_key,
                                sku_key,
                                qty,
                            ),
                        )
                        status = "RESERVED"

            elif op == "cancel":
                row = conn.execute(
                    """
                    SELECT sku, qty, state
                    FROM reservations
                    WHERE reservation_id = ?
                    """,
                    (reservation_key,),
                ).fetchone()

                if row is None:
                    status = "NOT_FOUND"

                else:
                    sku_key, qty, state = row

                    if state != "RESERVED":
                        status = "CONFLICT"

                    else:
                        conn.execute(
                            """
                            UPDATE reservations
                               SET state = 'CANCELLED'
                             WHERE reservation_id = ?
                            """,
                            (reservation_key,),
                        )

                        conn.execute(
                            """
                            UPDATE stock
                               SET available = available + ?
                             WHERE sku = ?
                            """,
                            (qty, sku_key),
                        )

                        status = "CANCELLED"

            else:  # ship
                row = conn.execute(
                    """
                    SELECT state
                    FROM reservations
                    WHERE reservation_id = ?
                    """,
                    (reservation_key,),
                ).fetchone()

                if row is None:
                    status = "NOT_FOUND"

                elif row[0] != "RESERVED":
                    status = "CONFLICT"

                else:
                    conn.execute(
                        """
                        UPDATE reservations
                           SET state = 'SHIPPED'
                         WHERE reservation_id = ?
                        """,
                        (reservation_key,),
                    )

                    status = "SHIPPED"

            # 成功だけでなく業務失敗も再送結果として保存する。
            conn.execute(
                """
                INSERT INTO request_log(
                    request_id,
                    command,
                    status
                )
                VALUES (?, ?, ?)
                """,
                (
                    request_key,
                    canonical,
                    status,
                ),
            )

            results.append(
                {
                    "request_id": request_id,
                    "status": status,
                }
            )

        # 全コマンド処理済み、まだCOMMIT前。
        if before_commit is not None:
            before_commit()

        conn.commit()

        # COMMIT成功後のみ結果を呼出し側へ返す。
        return results

    except BaseException:
        if conn.in_transaction:
            try:
                conn.rollback()
            except sqlite3.Error:
                pass
        raise

    finally:
        conn.close()


def snapshot(path) -> dict:
    conn = _connect(path)

    try:
        # 最初のSELECTで確立されたread snapshotをCOMMITまで維持する。
        # したがって複数SELECTでも同一時点を観測する。
        conn.execute("BEGIN")

        available_rows = conn.execute(
            """
            SELECT sku, available
            FROM stock
            ORDER BY sku
            """
        ).fetchall()

        reservation_rows = conn.execute(
            """
            SELECT
                reservation_id,
                sku,
                qty,
                state
            FROM reservations
            ORDER BY reservation_id
            """
        ).fetchall()

        result = {
            "available": {
                _from_key(sku): available
                for sku, available in available_rows
            },
            "reservations": {
                _from_key(reservation_id): {
                    "sku": _from_key(sku),
                    "qty": qty,
                    "state": state,
                }
                for (
                    reservation_id,
                    sku,
                    qty,
                    state,
                ) in reservation_rows
            },
        }

        conn.commit()
        return result

    except BaseException:
        if conn.in_transaction:
            try:
                conn.rollback()
            except sqlite3.Error:
                pass
        raise

    finally:
        conn.close()
