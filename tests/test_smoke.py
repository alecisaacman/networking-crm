import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from networking_crm.db import initialize_database, list_notes_for_contact
from networking_crm.main import main


class DatabaseBootstrapTest(unittest.TestCase):
    def test_initialize_database_creates_sqlite_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            db_path = tmp_path / "networking.db"
            schema_path = tmp_path / "schema.sql"
            schema_path.write_text(
                "create table if not exists contacts (id integer primary key);",
                encoding="utf-8",
            )

            created_path = initialize_database(db_path=db_path, schema_path=schema_path)

            self.assertEqual(created_path, db_path)
            self.assertTrue(db_path.exists())

    def test_add_contact_and_list_contacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            db_path = tmp_path / "networking.db"
            schema_path = ROOT / "config" / "schema.sql"
            initialize_database(db_path=db_path, schema_path=schema_path)

            add_output = StringIO()
            with redirect_stdout(add_output):
                exit_code = main(
                    [
                        "add-contact",
                        "--name",
                        "Ada Lovelace",
                        "--company",
                        "Analytical Engines",
                        "--role",
                        "Researcher",
                        "--source",
                        "Coffee chat",
                    ],
                    db_path=db_path,
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("Added contact #1: Ada Lovelace", add_output.getvalue())

            list_output = StringIO()
            with redirect_stdout(list_output):
                exit_code = main(["list-contacts"], db_path=db_path)

            rendered = list_output.getvalue()
            self.assertEqual(exit_code, 0)
            self.assertIn("#1 | Ada Lovelace | Analytical Engines | Researcher", rendered)
            self.assertIn("source=Coffee chat", rendered)

    def test_add_note_attaches_to_existing_contact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            db_path = tmp_path / "networking.db"
            schema_path = ROOT / "config" / "schema.sql"
            initialize_database(db_path=db_path, schema_path=schema_path)
            main(["add-contact", "--name", "Grace Hopper"], db_path=db_path)

            add_note_output = StringIO()
            with redirect_stdout(add_note_output):
                exit_code = main(
                    ["add-note", "--contact-id", "1", "--body", "Met at systems meetup."],
                    db_path=db_path,
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("Added note #1 to contact #1", add_note_output.getvalue())

            notes = list_notes_for_contact(contact_id=1, db_path=db_path)
            self.assertEqual(len(notes), 1)
            self.assertEqual(notes[0]["body"], "Met at systems meetup.")

    def test_add_note_rejects_unknown_contact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            db_path = tmp_path / "networking.db"
            schema_path = ROOT / "config" / "schema.sql"
            initialize_database(db_path=db_path, schema_path=schema_path)

            add_note_output = StringIO()
            with redirect_stdout(add_note_output):
                exit_code = main(
                    ["add-note", "--contact-id", "999", "--body", "Should fail."],
                    db_path=db_path,
                )

            self.assertEqual(exit_code, 1)
            self.assertIn("Contact #999 does not exist.", add_note_output.getvalue())

    def test_add_followup_attaches_to_existing_contact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            db_path = tmp_path / "networking.db"
            schema_path = ROOT / "config" / "schema.sql"
            initialize_database(db_path=db_path, schema_path=schema_path)
            main(["add-contact", "--name", "Katherine Johnson"], db_path=db_path)

            add_followup_output = StringIO()
            with redirect_stdout(add_followup_output):
                exit_code = main(
                    [
                        "add-followup",
                        "--contact-id",
                        "1",
                        "--due-on",
                        "2026-04-10",
                        "--reason",
                        "Send intro email.",
                    ],
                    db_path=db_path,
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("Added follow-up #1 to contact #1", add_followup_output.getvalue())

    def test_add_followup_rejects_unknown_contact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            db_path = tmp_path / "networking.db"
            schema_path = ROOT / "config" / "schema.sql"
            initialize_database(db_path=db_path, schema_path=schema_path)

            add_followup_output = StringIO()
            with redirect_stdout(add_followup_output):
                exit_code = main(
                    [
                        "add-followup",
                        "--contact-id",
                        "999",
                        "--due-on",
                        "2026-04-10",
                        "--reason",
                        "Should fail.",
                    ],
                    db_path=db_path,
                )

            self.assertEqual(exit_code, 1)
            self.assertIn("Contact #999 does not exist.", add_followup_output.getvalue())

    def test_list_followups_sorts_by_due_date(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            db_path = tmp_path / "networking.db"
            schema_path = ROOT / "config" / "schema.sql"
            initialize_database(db_path=db_path, schema_path=schema_path)
            main(["add-contact", "--name", "Ada Lovelace"], db_path=db_path)
            main(["add-contact", "--name", "Grace Hopper"], db_path=db_path)
            main(
                [
                    "add-followup",
                    "--contact-id",
                    "1",
                    "--due-on",
                    "2026-04-12",
                    "--reason",
                    "Later follow-up.",
                ],
                db_path=db_path,
            )
            main(
                [
                    "add-followup",
                    "--contact-id",
                    "2",
                    "--due-on",
                    "2026-04-09",
                    "--reason",
                    "Sooner follow-up.",
                ],
                db_path=db_path,
            )

            list_output = StringIO()
            with redirect_stdout(list_output):
                exit_code = main(["list-followups"], db_path=db_path)

            rendered_lines = [line for line in list_output.getvalue().splitlines() if line.startswith("#")]
            self.assertEqual(exit_code, 0)
            self.assertEqual(
                rendered_lines,
                [
                    "#2 | contact=#2 | Grace Hopper | due=2026-04-09",
                    "#1 | contact=#1 | Ada Lovelace | due=2026-04-12",
                ],
            )

    def test_due_command_filters_overdue_and_today_followups(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            db_path = tmp_path / "networking.db"
            schema_path = ROOT / "config" / "schema.sql"
            initialize_database(db_path=db_path, schema_path=schema_path)
            main(["add-contact", "--name", "Margaret Hamilton"], db_path=db_path)
            main(
                [
                    "add-followup",
                    "--contact-id",
                    "1",
                    "--due-on",
                    "2026-04-06",
                    "--reason",
                    "Overdue item.",
                ],
                db_path=db_path,
            )
            main(
                [
                    "add-followup",
                    "--contact-id",
                    "1",
                    "--due-on",
                    "2026-04-07",
                    "--reason",
                    "Due today.",
                ],
                db_path=db_path,
            )
            main(
                [
                    "add-followup",
                    "--contact-id",
                    "1",
                    "--due-on",
                    "2026-04-08",
                    "--reason",
                    "Future item.",
                ],
                db_path=db_path,
            )

            due_output = StringIO()
            with patch("networking_crm.main.date") as mock_date:
                mock_date.today.return_value.isoformat.return_value = "2026-04-07"
                with redirect_stdout(due_output):
                    exit_code = main(["due"], db_path=db_path)

            rendered = due_output.getvalue()
            self.assertEqual(exit_code, 0)
            self.assertIn("#1 | contact=#1 | Margaret Hamilton | due=2026-04-06", rendered)
            self.assertIn("#2 | contact=#1 | Margaret Hamilton | due=2026-04-07", rendered)
            self.assertNotIn("due=2026-04-08", rendered)


if __name__ == "__main__":
    unittest.main()
