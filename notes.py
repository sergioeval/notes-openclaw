#!/usr/bin/env python3
"""Simple notes CLI backed by SQLite."""

from __future__ import annotations

import argparse
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

DB_PATH = Path(__file__).with_name("notes.sqlite3")


@dataclass(frozen=True)
class Note:
    id: int
    created_at: str
    title: str
    body: str
    pinned: int


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                title TEXT NOT NULL,
                body TEXT NOT NULL DEFAULT '',
                pinned INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.commit()


def add_note(title: str, body: str = "") -> int:
    init_db()
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO notes (created_at, title, body, pinned) VALUES (?, ?, ?, 0)",
            (created_at, title, body),
        )
        conn.commit()
        return int(cur.lastrowid)


def list_notes(include_pinned: bool = True) -> list[Note]:
    init_db()
    query = "SELECT id, created_at, title, body, pinned FROM notes"
    if not include_pinned:
        query += " WHERE pinned = 0"
    query += " ORDER BY pinned DESC, created_at DESC, id DESC"
    with connect() as conn:
        rows = conn.execute(query).fetchall()
    return [Note(**dict(row)) for row in rows]


def pin_note(note_id: int) -> bool:
    init_db()
    with connect() as conn:
        cur = conn.execute("UPDATE notes SET pinned = 1 WHERE id = ?", (note_id,))
        conn.commit()
        return cur.rowcount > 0


def delete_note(note_id: int) -> bool:
    init_db()
    with connect() as conn:
        cur = conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        conn.commit()
        return cur.rowcount > 0


def print_notes(rows: Iterable[Note]) -> None:
    items = list(rows)
    if not items:
        print("No notes found.")
        return

    print(f"{'ID':>4}  {'Created at':<20}  {'Pinned':<6}  Title  Body")
    print("-" * 80)
    for item in items:
        pinned = "yes" if item.pinned else "no"
        print(f"{item.id:>4}  {item.created_at[:19]:<20}  {pinned:<6}  {item.title}  {item.body}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simple notes CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add a note")
    add_parser.add_argument("title", help="Note title")
    add_parser.add_argument("body", nargs="?", default="", help="Optional note body")

    list_parser = subparsers.add_parser("list", help="List notes")
    list_parser.add_argument("--unpinned-only", action="store_true", help="Show only unpinned notes")

    pin_parser = subparsers.add_parser("pin", help="Pin a note")
    pin_parser.add_argument("id", type=int, help="Note ID")

    delete_parser = subparsers.add_parser("delete", help="Delete a note")
    delete_parser.add_argument("id", type=int, help="Note ID")

    subparsers.add_parser("init", help="Initialize the database")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.command == "init":
        init_db()
        print(f"Database ready at {DB_PATH}")
        return

    if args.command == "add":
        note_id = add_note(args.title, args.body)
        print(f"Recorded note #{note_id}")
        return

    if args.command == "list":
        print_notes(list_notes(include_pinned=not args.unpinned_only))
        return

    if args.command == "pin":
        if pin_note(args.id):
            print(f"Pinned note #{args.id}")
        else:
            print(f"Note #{args.id} not found")
        return

    if args.command == "delete":
        if delete_note(args.id):
            print(f"Deleted note #{args.id}")
        else:
            print(f"Note #{args.id} not found")
        return


if __name__ == "__main__":
    main()
