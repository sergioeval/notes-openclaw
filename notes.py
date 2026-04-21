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
    tags: str
    pinned: int
    archived: int


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row[1] == column for row in rows)


def init_db() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                title TEXT NOT NULL,
                body TEXT NOT NULL DEFAULT '',
                tags TEXT NOT NULL DEFAULT '',
                pinned INTEGER NOT NULL DEFAULT 0,
                archived INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        if not column_exists(conn, "notes", "tags"):
            conn.execute("ALTER TABLE notes ADD COLUMN tags TEXT NOT NULL DEFAULT ''")
        if not column_exists(conn, "notes", "pinned"):
            conn.execute("ALTER TABLE notes ADD COLUMN pinned INTEGER NOT NULL DEFAULT 0")
        if not column_exists(conn, "notes", "archived"):
            conn.execute("ALTER TABLE notes ADD COLUMN archived INTEGER NOT NULL DEFAULT 0")
        conn.commit()


def add_note(title: str, body: str = "", tags: str = "") -> int:
    init_db()
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO notes (created_at, title, body, tags, pinned, archived) VALUES (?, ?, ?, ?, 0, 0)",
            (created_at, title, body, tags),
        )
        conn.commit()
        return int(cur.lastrowid)


def edit_note(note_id: int, title: str | None = None, body: str | None = None, tags: str | None = None) -> bool:
    init_db()
    updates = []
    params: list[object] = []
    if title is not None:
        updates.append("title = ?")
        params.append(title)
    if body is not None:
        updates.append("body = ?")
        params.append(body)
    if tags is not None:
        updates.append("tags = ?")
        params.append(tags)
    if not updates:
        return False
    params.append(note_id)
    with connect() as conn:
        cur = conn.execute(f"UPDATE notes SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
        return cur.rowcount > 0


def list_notes(include_pinned: bool = True, include_archived: bool = True) -> list[Note]:
    init_db()
    query = "SELECT id, created_at, title, body, tags, pinned, archived FROM notes"
    clauses = []
    if not include_pinned:
        clauses.append("pinned = 0")
    if not include_archived:
        clauses.append("archived = 0")
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY pinned DESC, archived ASC, created_at DESC, id DESC"
    with connect() as conn:
        rows = conn.execute(query).fetchall()
    return [Note(**dict(row)) for row in rows]


def set_flag(note_id: int, field: str, value: int) -> bool:
    init_db()
    with connect() as conn:
        cur = conn.execute(f"UPDATE notes SET {field} = ? WHERE id = ?", (value, note_id))
        conn.commit()
        return cur.rowcount > 0


def pin_note(note_id: int) -> bool:
    return set_flag(note_id, "pinned", 1)


def archive_note(note_id: int) -> bool:
    return set_flag(note_id, "archived", 1)


def unarchive_note(note_id: int) -> bool:
    return set_flag(note_id, "archived", 0)


def delete_note(note_id: int) -> bool:
    init_db()
    with connect() as conn:
        cur = conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        conn.commit()
        return cur.rowcount > 0


def search_notes(query_text: str) -> list[Note]:
    init_db()
    pattern = f"%{query_text}%"
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, created_at, title, body, tags, pinned, archived
            FROM notes
            WHERE title LIKE ? OR body LIKE ? OR tags LIKE ?
            ORDER BY pinned DESC, archived ASC, created_at DESC, id DESC
            """,
            (pattern, pattern, pattern),
        ).fetchall()
    return [Note(**dict(row)) for row in rows]


def print_notes(rows: Iterable[Note]) -> None:
    items = list(rows)
    if not items:
        print("No notes found.")
        return

    print(f"{'ID':>4}  {'Created at':<20}  {'Pinned':<6}  {'Arch':<5}  Title  Tags  Body")
    print("-" * 100)
    for item in items:
        pinned = "yes" if item.pinned else "no"
        archived = "yes" if item.archived else "no"
        print(f"{item.id:>4}  {item.created_at[:19]:<20}  {pinned:<6}  {archived:<5}  {item.title}  {item.tags}  {item.body}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simple notes CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add a note")
    add_parser.add_argument("title", help="Note title")
    add_parser.add_argument("body", nargs="?", default="", help="Optional note body")
    add_parser.add_argument("--tags", default="", help="Comma-separated tags")

    edit_parser = subparsers.add_parser("edit", help="Edit a note")
    edit_parser.add_argument("id", type=int, help="Note ID")
    edit_parser.add_argument("--title", default=None, help="New title")
    edit_parser.add_argument("--body", default=None, help="New body")
    edit_parser.add_argument("--tags", default=None, help="New comma-separated tags")

    list_parser = subparsers.add_parser("list", help="List notes")
    list_parser.add_argument("--unpinned-only", action="store_true", help="Show only unpinned notes")
    list_parser.add_argument("--unarchived-only", action="store_true", help="Show only unarchived notes")

    search_parser = subparsers.add_parser("search", help="Search notes")
    search_parser.add_argument("query", help="Search text")

    pin_parser = subparsers.add_parser("pin", help="Pin a note")
    pin_parser.add_argument("id", type=int, help="Note ID")

    archive_parser = subparsers.add_parser("archive", help="Archive a note")
    archive_parser.add_argument("id", type=int, help="Note ID")

    unarchive_parser = subparsers.add_parser("unarchive", help="Unarchive a note")
    unarchive_parser.add_argument("id", type=int, help="Note ID")

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
        note_id = add_note(args.title, args.body, args.tags)
        print(f"Recorded note #{note_id}")
        return

    if args.command == "edit":
        if edit_note(args.id, args.title, args.body, args.tags):
            print(f"Updated note #{args.id}")
        else:
            print(f"Note #{args.id} not found or nothing to update")
        return

    if args.command == "list":
        print_notes(list_notes(include_pinned=not args.unpinned_only, include_archived=not args.unarchived_only))
        return

    if args.command == "search":
        print_notes(search_notes(args.query))
        return

    if args.command == "pin":
        if pin_note(args.id):
            print(f"Pinned note #{args.id}")
        else:
            print(f"Note #{args.id} not found")
        return

    if args.command == "archive":
        if archive_note(args.id):
            print(f"Archived note #{args.id}")
        else:
            print(f"Note #{args.id} not found")
        return

    if args.command == "unarchive":
        if unarchive_note(args.id):
            print(f"Unarchived note #{args.id}")
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
