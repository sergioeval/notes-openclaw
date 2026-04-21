#!/usr/bin/env python3
"""Simple reminder watcher."""

from __future__ import annotations

from notes import due_notes


def build_message() -> str:
    items = due_notes()
    if not items:
        return "No due reminders."

    lines = ["Due reminders:"]
    for item in items:
        due = item.remind_at or ""
        lines.append(f"- #{item.id} {item.title} (due: {due})")
        if item.body:
            lines.append(f"  {item.body}")
    return "\n".join(lines)


def main() -> None:
    print(build_message())


if __name__ == "__main__":
    main()
