from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable
from os import PathLike
from typing import Any

_MAX_QTY = 10**9
_MAX_TEXT = 128
_BUSY_TIMEOUT_MS = 5_000

_RESERVE_KEYS = {"request_id", "op", "reservation_id", "sku", "qty"}
_TERMINAL_KEYS = {"request_id", "op", "reservation_id"}


def _is_text(value: object) -> bool:
    return isinstance(value, str) and 1 <= len(value) <= _MAX_TEXT


def _is_int_in_range(value: object, low: int, high: int) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and low <= value <= high


def _connect(path: str | bytes | PathLike[str] | PathLike[bytes]) -> sqlite3.Connection:
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


def _validate_stocks(stocks: object) -> list[tuple[str, int]]:
    if not isinstance(stocks, dict) or not stocks:
        raise ValueError("stocks must be a non-empty dict")

    rows: list[tuple[str, int]] = []
    for sku, qty in stocks.items():
        if not _is_text(sku):
            raise ValueError("each SKU must be a str of length 1..128")
        if not _is_int_in_range(qty, 0, _MAX_QTY):
            raise ValueError(
                "each initial stock must be an int in 0..10^9 "
                "(bool is not allowed)"
            )
        rows.append((sku, qty))
    return rows


def _validate_commands(commands: object) -> list[tuple[dict[str, Any], str, int]]:
    if not isinstance(commands, list) or not commands:
        raise ValueError("commands must be a non-empty list")

    validated: list[tuple[dict[str, Any], str, int]] = []

    for index, raw in enumerate(commands):
        if not isinstance(raw, dict):
            raise ValueError(f"commands[{index}] must be a dict")

        op = raw.get("op")
        if op not in ("reserve", "cancel", "ship"):
            raise ValueError(f"commands[{index}] has an invalid op")

        expected_keys = _RESERVE_KEYS if op == "reserve" else _TERMINAL_KEYS
        if set(raw) != expected_keys:
            raise ValueError(f"commands[{index}] has invalid keys")

        request_id = raw["request_id"]
        reservation_id = raw["reservation_id"]

        if not _is_text(request_id):
            raise ValueError(
                f"commands[{index}].request_id must be a str of length 1..128"
            )
        if not _is_text(reservation_id):
            raise ValueError(
                f"commands[{index}].reservation_id must be a str of length 1..128"
            )

        if op == "reserve":
            sku = raw["sku"]
            qty = raw["qty"]

            if not _is_text(sku):
                raise ValueError(
                    f"commands[{index}].sku must be a str of length 1..128"
                )
            if not _is_int_in_range(qty, 1, _MAX_QTY):
                raise ValueError(
                    f"commands[{index}].qty must be an int in 1..10^9 "
                    "(bool is not allowed)"
                )

            command = {
                "request_id": request_id,
                "op": op,
                "reservation_id": reservation_id,
                "sku": sku,
                "qty": qty,
            }
        else:
            command = {
                "request_id": request_id,
                "op": op,
                "reservation_id": reservation_id,
            }

        canonical = json.dumps(
            command,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        validated.append((command, canonical, index))

    return validated


def init_db(path, stocks) -> None:
    rows = _validate_stocks(stocks)

    conn = _connect(path)
    in_transaction = False

    try:
        # init_db は新規DBに対して一度だけ、非並行で呼ばれる前提。
        # WAL は永続設定であり、snapshot の読み取りと writer の共存にも適する。
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = FULL")

        conn.execute("BEGIN IMMEDIATE")
        in_transaction = True

        conn.execute(
            """
            CREATE TABLE stocks (
                sku TEXT COLLATE BINARY NOT NULL PRIMARY KEY,
                available INTEGER NOT NULL
                    CHECK (
                        typeof(available) = 'integer'
                        AND available BETWEEN 0 AND 1000000000
                    )
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE reservations (
                reservation_id TEXT COLLATE BINARY NOT NULL PRIMARY KEY,
                sku TEXT COLLATE BINARY NOT NULL,
                qty INTEGER NOT NULL
                    CHECK (
                        typeof(qty) = 'integer'
                        AND qty BETWEEN 1 AND 1000000000
                    ),
                state TEXT NOT NULL
                    CHECK (state IN ('RESERVED', 'CANCELLED', 'SHIPPED')),
                FOREIGN KEY (sku) REFERENCES stocks(sku)
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE requests (
                request_id TEXT COLLATE BINARY NOT NULL PRIMARY KEY,
                canonical_command TEXT NOT NULL,
                status TEXT NOT NULL
                    CHECK (
                        status IN (
                            'RESERVED',
                            'OUT_OF_STOCK',
                            'CANCELLED',
                            'SHIPPED',
                            'NOT_FOUND',
                            'CONFLICT'
                        )
                    )
            )
            """
        )

        conn.executemany(
            "INSERT INTO stocks(sku, available) VALUES (?, ?)",
            rows,
        )

        conn.execute("COMMIT")
        in_transaction = False

    except BaseException:
        if in_transaction:
            try:
                conn.execute("ROLLBACK")
            except sqlite3.Error:
                pass
        raise

    finally:
        conn.close()


def _apply_new_command(
    conn: sqlite3.Connection,
    command: dict[str, Any],
) -> str:
    op = command["op"]
    reservation_id = command["reservation_id"]

    if op == "reserve":
        # 在庫判定より予約ID衝突を優先する。
        exists = conn.execute(
            """
            SELECT 1
              FROM reservations
             WHERE reservation_id = ?
            """,
            (reservation_id,),
        ).fetchone()

        if exists is not None:
            return "CONFLICT"

        sku = command["sku"]
        qty = command["qty"]

        # 在庫確認と減算を1 UPDATEで行う。
        cursor = conn.execute(
            """
            UPDATE stocks
               SET available = available - ?
             WHERE sku = ?
               AND available >= ?
            """,
            (qty, sku, qty),
        )

        if cursor.rowcount != 1:
            return "OUT_OF_STOCK"

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
            (reservation_id, sku, qty),
        )

        return "RESERVED"

    row = conn.execute(
        """
        SELECT sku, qty, state
          FROM reservations
         WHERE reservation_id = ?
        """,
        (reservation_id,),
    ).fetchone()

    if row is None:
        return "NOT_FOUND"

    sku, qty, state = row

    if state != "RESERVED":
        return "CONFLICT"

    if op == "cancel":
        cursor = conn.execute(
            """
            UPDATE reservations
               SET state = 'CANCELLED'
             WHERE reservation_id = ?
               AND state = 'RESERVED'
            """,
            (reservation_id,),
        )

        if cursor.rowcount != 1:
            raise sqlite3.DatabaseError(
                "reservation state changed unexpectedly"
            )

        cursor = conn.execute(
            """
            UPDATE stocks
               SET available = available + ?
             WHERE sku = ?
            """,
            (qty, sku),
        )

        if cursor.rowcount != 1:
            raise sqlite3.DatabaseError(
                "reservation refers to a missing SKU"
            )

        return "CANCELLED"

    if op == "ship":
        cursor = conn.execute(
            """
            UPDATE reservations
               SET state = 'SHIPPED'
             WHERE reservation_id = ?
               AND state = 'RESERVED'
            """,
            (reservation_id,),
        )

        if cursor.rowcount != 1:
            raise sqlite3.DatabaseError(
                "reservation state changed unexpectedly"
            )

        return "SHIPPED"

    raise sqlite3.DatabaseError(
        "invalid operation reached execution"
    )


def apply_batch(
    path,
    commands,
    *,
    before_commit: Callable[[], object] | None = None,
) -> list[dict]:
    # 型・キー・op・範囲はDB操作や再送判定より先に検査する。
    validated = _validate_commands(commands)

    conn = _connect(path)
    in_transaction = False

    try:
        # SQLiteのプロセス間write lockを最初に取得する。
        # 成功するwriter batchはこれにより直列化される。
        conn.execute("BEGIN IMMEDIATE")
        in_transaction = True

        # 未登録SKU検査も request_id の再送判定より先に行う。
        checked_skus: set[str] = set()

        for command, _canonical, index in validated:
            if command["op"] != "reserve":
                continue

            sku = command["sku"]

            if sku in checked_skus:
                continue

            checked_skus.add(sku)

            row = conn.execute(
                """
                SELECT 1
                  FROM stocks
                 WHERE sku = ?
                """,
                (sku,),
            ).fetchone()

            if row is None:
                raise ValueError(
                    f"commands[{index}] refers to an unknown SKU"
                )

        results: list[dict] = []

        # 入力順に処理するので、後続commandは先行commandの更新を見る。
        for command, canonical, _index in validated:
            request_id = command["request_id"]

            previous = conn.execute(
                """
                SELECT canonical_command, status
                  FROM requests
                 WHERE request_id = ?
                """,
                (request_id,),
            ).fetchone()

            if previous is not None:
                previous_command, previous_status = previous

                if previous_command != canonical:
                    raise ValueError(
                        f"request_id {request_id!r} "
                        "was already used for different content"
                    )

                # 成功・失敗を問わず最初にcommitされた結果をそのまま返す。
                status = previous_status

            else:
                status = _apply_new_command(conn, command)

                # 業務失敗も含め、結果と正規化済みcommandを同じtransactionに保存。
                conn.execute(
                    """
                    INSERT INTO requests(
                        request_id,
                        canonical_command,
                        status
                    )
                    VALUES (?, ?, ?)
                    """,
                    (request_id, canonical, status),
                )

            results.append(
                {
                    "request_id": request_id,
                    "status": status,
                }
            )

        # 全command処理後、COMMIT直前にちょうど1回。
        if before_commit is not None:
            before_commit()

        conn.execute("COMMIT")
        in_transaction = False

        # commit完了後にのみ成功結果を呼出し側へ返す。
        return results

    except BaseException:
        if in_transaction:
            try:
                conn.execute("ROLLBACK")
            except sqlite3.Error:
                pass
        raise

    finally:
        conn.close()


def snapshot(path) -> dict:
    conn = _connect(path)
    in_transaction = False

    try:
        # 複数SELECTを同じread transactionに置く。
        # 最初のSELECTで確立したSQLite snapshotを最後まで保持する。
        conn.execute("BEGIN")
        in_transaction = True

        stock_rows = conn.execute(
            """
            SELECT sku, available
              FROM stocks
             ORDER BY sku COLLATE BINARY
            """
        ).fetchall()

        reservation_rows = conn.execute(
            """
            SELECT reservation_id, sku, qty, state
              FROM reservations
             ORDER BY reservation_id COLLATE BINARY
            """
        ).fetchall()

        result = {
            "available": {
                sku: available
                for sku, available in stock_rows
            },
            "reservations": {
                reservation_id: {
                    "sku": sku,
                    "qty": qty,
                    "state": state,
                }
                for reservation_id, sku, qty, state
                in reservation_rows
            },
        }

        conn.execute("COMMIT")
        in_transaction = False

        return result

    except BaseException:
        if in_transaction:
            try:
                conn.execute("ROLLBACK")
            except sqlite3.Error:
                pass
        raise

    finally:
        conn.close()
