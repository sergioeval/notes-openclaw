# Notes OpenClaw

A simple Python CLI for notes backed by SQLite.

## Commands

Initialize the database:

```bash
python3 notes.py init
```

Add a note:

```bash
python3 notes.py add "Meeting ideas" "follow up on the UI" --tags work,ui
```

Edit a note:

```bash
python3 notes.py edit 1 --title "Updated title" --body "new text" --tags personal,important
```

List notes:

```bash
python3 notes.py list
```

List only unpinned notes:

```bash
python3 notes.py list --unpinned-only
```

List only unarchived notes:

```bash
python3 notes.py list --unarchived-only
```

Search notes:

```bash
python3 notes.py search ui
```

Pin a note:

```bash
python3 notes.py pin 1
```

Archive a note:

```bash
python3 notes.py archive 1
```

Unarchive a note:

```bash
python3 notes.py unarchive 1
```

Delete a note:

```bash
python3 notes.py delete 1
```

## Storage

The SQLite database is stored locally as:

```text
notes.sqlite3
```

It is ignored by git and should not be committed.
