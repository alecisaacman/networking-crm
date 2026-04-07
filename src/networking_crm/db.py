import sqlite3
from pathlib import Path
from typing import Optional

from .paths import ARTIFACTS_DIR, DB_PATH, LOGS_DIR, SCHEMA_PATH, STATE_DIR


def ensure_runtime_dirs() -> None:
    for path in (STATE_DIR, LOGS_DIR, ARTIFACTS_DIR):
        path.mkdir(parents=True, exist_ok=True)


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    ensure_runtime_dirs()
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("pragma foreign_keys = on")
    return connection


def initialize_database(db_path: Path = DB_PATH, schema_path: Path = SCHEMA_PATH) -> Path:
    ensure_runtime_dirs()
    schema_sql = schema_path.read_text(encoding="utf-8")
    with get_connection(db_path) as connection:
        connection.executescript(schema_sql)
        connection.commit()
    return db_path


def add_contact(
    full_name: str,
    company: Optional[str] = None,
    role_title: Optional[str] = None,
    location: Optional[str] = None,
    source: Optional[str] = None,
    email: Optional[str] = None,
    linkedin_url: Optional[str] = None,
    db_path: Path = DB_PATH,
) -> int:
    with get_connection(db_path) as connection:
        cursor = connection.execute(
            """
            insert into contacts (
                full_name,
                company,
                role_title,
                location,
                source,
                email,
                linkedin_url
            ) values (?, ?, ?, ?, ?, ?, ?)
            """,
            (full_name, company, role_title, location, source, email, linkedin_url),
        )
        connection.commit()
        return int(cursor.lastrowid)


def list_contacts(db_path: Path = DB_PATH) -> list[sqlite3.Row]:
    with get_connection(db_path) as connection:
        cursor = connection.execute(
            """
            select
                id,
                full_name,
                company,
                role_title,
                location,
                source,
                email,
                linkedin_url,
                created_at,
                updated_at
            from contacts
            order by full_name collate nocase asc, id asc
            """
        )
        return list(cursor.fetchall())


def contact_exists(contact_id: int, db_path: Path = DB_PATH) -> bool:
    with get_connection(db_path) as connection:
        row = connection.execute(
            "select 1 from contacts where id = ?",
            (contact_id,),
        ).fetchone()
    return row is not None


def add_note(contact_id: int, body: str, db_path: Path = DB_PATH) -> int:
    with get_connection(db_path) as connection:
        cursor = connection.execute(
            "insert into notes (contact_id, body) values (?, ?)",
            (contact_id, body),
        )
        connection.commit()
        return int(cursor.lastrowid)


def list_notes_for_contact(contact_id: int, db_path: Path = DB_PATH) -> list[sqlite3.Row]:
    with get_connection(db_path) as connection:
        cursor = connection.execute(
            """
            select id, contact_id, body, created_at
            from notes
            where contact_id = ?
            order by created_at asc, id asc
            """,
            (contact_id,),
        )
        return list(cursor.fetchall())
