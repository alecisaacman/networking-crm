import argparse
from pathlib import Path
from typing import List, Optional

from .main import (
    handle_due,
    handle_list_contacts,
    handle_show_contact,
    handle_today,
)
from .paths import DB_PATH


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ari",
        description="ARI command surface for the networking CRM module.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("today", help="Show today's follow-up summary.")

    contacts_parser = subparsers.add_parser("contacts", help="Contact commands.")
    contacts_subparsers = contacts_parser.add_subparsers(dest="contacts_command", required=True)
    contacts_subparsers.add_parser("list", help="List saved contacts.")
    contacts_show_parser = contacts_subparsers.add_parser("show", help="Show a contact with notes and follow-ups.")
    contacts_show_parser.add_argument("--id", type=int, required=True, help="Existing contact id.")

    followups_parser = subparsers.add_parser("followups", help="Follow-up commands.")
    followups_subparsers = followups_parser.add_subparsers(dest="followups_command", required=True)
    followups_subparsers.add_parser("due", help="Show overdue and today's pending follow-ups.")

    return parser


def main(argv: Optional[List[str]] = None, db_path: Path = DB_PATH) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "today":
        return handle_today(db_path=db_path)
    if args.command == "contacts" and args.contacts_command == "list":
        return handle_list_contacts(db_path=db_path)
    if args.command == "contacts" and args.contacts_command == "show":
        return handle_show_contact(args, db_path=db_path)
    if args.command == "followups" and args.followups_command == "due":
        return handle_due(db_path=db_path)

    parser.error("Unknown ARI command.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
