# networking-crm

Local Mac tool to track networking contacts, follow-ups, and notes.

## Why this shape

This project starts as a Python CLI backed by SQLite.
That keeps setup minimal while giving a clean path to richer workflows later.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
networking-crm init-db
networking-crm status
```

For direct local runs without installation:

```bash
PYTHONPATH=src python3 -m networking_crm init-db
PYTHONPATH=src python3 -m networking_crm status
```

## Initial commands

* `networking-crm init-db`
* `networking-crm status`

## Layout

* `src/networking_crm/` application code
* `tests/` starter tests
* `config/schema.sql` SQLite schema
* `runtime/` local database, logs, and artifacts
* `docs/` product and implementation context

## Next implementation move

Build the first real contact workflow:

1. add a contact
2. list contacts
3. capture notes and follow-up dates
