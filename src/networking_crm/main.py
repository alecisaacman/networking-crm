import argparse
from pathlib import Path
from typing import List, Optional

from .db import add_contact, add_note, contact_exists, initialize_database, list_contacts
from .paths import DB_PATH


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="networking-crm",
        description="Track networking contacts, follow-ups, and notes locally.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-db", help="Create the local SQLite database.")
    subparsers.add_parser("status", help="Show the current local project status.")

    add_contact_parser = subparsers.add_parser("add-contact", help="Add a networking contact.")
    add_contact_parser.add_argument("--name", required=True, help="Full name for the contact.")
    add_contact_parser.add_argument("--company", help="Company name.")
    add_contact_parser.add_argument("--role", dest="role_title", help="Role or title.")
    add_contact_parser.add_argument("--location", help="Location or city.")
    add_contact_parser.add_argument("--source", help="Where you met or found them.")
    add_contact_parser.add_argument("--email", help="Email address.")
    add_contact_parser.add_argument("--linkedin-url", help="LinkedIn profile URL.")

    subparsers.add_parser("list-contacts", help="List saved contacts.")

    add_note_parser = subparsers.add_parser("add-note", help="Attach a note to a contact.")
    add_note_parser.add_argument("--contact-id", type=int, required=True, help="Existing contact id.")
    add_note_parser.add_argument("--body", required=True, help="Note text.")

    return parser


def handle_init_db(db_path: Path = DB_PATH) -> int:
    db_path = initialize_database(db_path=db_path)
    print(f"Initialized database at {db_path}")
    return 0


def handle_status(db_path: Path = DB_PATH) -> int:
    exists = db_path.exists()
    print("Project: networking-crm")
    print(f"Database: {db_path}")
    print(f"Database initialized: {'yes' if exists else 'no'}")
    print("Current commands: init-db, status, add-contact, list-contacts, add-note.")
    return 0


def handle_add_contact(args: argparse.Namespace, db_path: Path = DB_PATH) -> int:
    contact_id = add_contact(
        full_name=args.name,
        company=args.company,
        role_title=args.role_title,
        location=args.location,
        source=args.source,
        email=args.email,
        linkedin_url=args.linkedin_url,
        db_path=db_path,
    )
    print(f"Added contact #{contact_id}: {args.name}")
    return 0


def handle_list_contacts(db_path: Path = DB_PATH) -> int:
    contacts = list_contacts(db_path=db_path)
    if not contacts:
        print("No contacts found.")
        return 0

    for contact in contacts:
        summary_parts = [f"#{contact['id']}", contact["full_name"]]
        if contact["company"]:
            summary_parts.append(contact["company"])
        if contact["role_title"]:
            summary_parts.append(contact["role_title"])
        print(" | ".join(summary_parts))

        detail_parts = []
        if contact["location"]:
            detail_parts.append(f"location={contact['location']}")
        if contact["source"]:
            detail_parts.append(f"source={contact['source']}")
        if contact["email"]:
            detail_parts.append(f"email={contact['email']}")
        if contact["linkedin_url"]:
            detail_parts.append(f"linkedin={contact['linkedin_url']}")
        if detail_parts:
            print(f"  {'; '.join(detail_parts)}")

    return 0


def handle_add_note(args: argparse.Namespace, db_path: Path = DB_PATH) -> int:
    if not contact_exists(args.contact_id, db_path=db_path):
        print(f"Contact #{args.contact_id} does not exist.")
        return 1

    note_id = add_note(contact_id=args.contact_id, body=args.body, db_path=db_path)
    print(f"Added note #{note_id} to contact #{args.contact_id}")
    return 0


def main(argv: Optional[List[str]] = None, db_path: Path = DB_PATH) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init-db":
        return handle_init_db(db_path=db_path)
    if args.command == "status":
        return handle_status(db_path=db_path)
    if args.command == "add-contact":
        return handle_add_contact(args, db_path=db_path)
    if args.command == "list-contacts":
        return handle_list_contacts(db_path=db_path)
    if args.command == "add-note":
        return handle_add_note(args, db_path=db_path)

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
