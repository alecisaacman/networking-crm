# networking-crm

Local-first CLI tool to track networking contacts, notes, and follow-ups.

Built with Python and SQLite. No external dependencies.

---

## Why this exists

Most networking tools are overbuilt, cloud-based, and slow to use.

This project focuses on:

* fast, single-user workflows
* local-first data ownership
* simple commands over complex interfaces

---

## Features

* Add contacts with relevant context (company, role, where you met)
* List contacts in a clean, readable format
* Attach notes to contacts
* Local SQLite storage (no external services)
* Zero dependencies (standard library only)

---

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

networking-crm init-db
networking-crm status
```

Or run without installing:

```bash
PYTHONPATH=src python3 -m networking_crm init-db
PYTHONPATH=src python3 -m networking_crm status
```

---

## Example usage

```bash
networking-crm add-contact \
  --name "Ada Lovelace" \
  --company "Analytical Engines" \
  --role "Researcher" \
  --source "Coffee chat"

networking-crm list-contacts

networking-crm add-note \
  --contact-id 1 \
  --body "Discussed systems tooling and follow-up ideas."
```

---

## Project structure

```
src/networking_crm/   # application code
tests/                # unit tests
config/               # schema
runtime/              # local database + logs
```

---

## Development

Run tests:

```bash
python3 -m unittest discover -s tests -v
```

---

## Status

Phase 1 complete:

* contacts
* notes
* CLI interface
* SQLite persistence
* test coverage

Next:

* follow-ups
* filtering / search

