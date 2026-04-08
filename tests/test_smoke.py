import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date as real_date
from io import StringIO
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from networking_crm.db import (
    get_connection,
    initialize_database,
    list_notes_for_contact,
)
from networking_crm.ari import main as ari_main
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

    def test_today_command_groups_overdue_due_today_and_upcoming(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            db_path = tmp_path / "networking.db"
            schema_path = ROOT / "config" / "schema.sql"
            initialize_database(db_path=db_path, schema_path=schema_path)
            main(["add-contact", "--name", "Annie Easley"], db_path=db_path)
            main(["add-contact", "--name", "Mary Jackson"], db_path=db_path)
            main(
                [
                    "add-followup",
                    "--contact-id",
                    "1",
                    "--due-on",
                    "2026-04-05",
                    "--reason",
                    "Past due intro.",
                ],
                db_path=db_path,
            )
            main(
                [
                    "add-followup",
                    "--contact-id",
                    "2",
                    "--due-on",
                    "2026-04-07",
                    "--reason",
                    "Reply today.",
                ],
                db_path=db_path,
            )
            main(
                [
                    "add-followup",
                    "--contact-id",
                    "1",
                    "--due-on",
                    "2026-04-09",
                    "--reason",
                    "Schedule coffee.",
                ],
                db_path=db_path,
            )
            main(
                [
                    "add-followup",
                    "--contact-id",
                    "2",
                    "--due-on",
                    "2026-04-14",
                    "--reason",
                    "Still in window.",
                ],
                db_path=db_path,
            )
            main(
                [
                    "add-followup",
                    "--contact-id",
                    "1",
                    "--due-on",
                    "2026-04-15",
                    "--reason",
                    "Outside window.",
                ],
                db_path=db_path,
            )

            today_output = StringIO()
            with patch("networking_crm.main.date") as mock_date:
                mock_date.today.return_value = real_date(2026, 4, 7)
                with redirect_stdout(today_output):
                    exit_code = main(["today"], db_path=db_path)

            rendered = today_output.getvalue()
            self.assertEqual(exit_code, 0)
            self.assertIn("Today", rendered)
            self.assertIn("Pending follow-ups: 5", rendered)
            self.assertIn("Overdue", rendered)
            self.assertIn("contact=#1 | Annie Easley | due=2026-04-05 | reason=Past due intro.", rendered)
            self.assertIn("Due Today", rendered)
            self.assertIn("contact=#2 | Mary Jackson | due=2026-04-07 | reason=Reply today.", rendered)
            self.assertIn("Upcoming (Next 7 Days)", rendered)
            self.assertIn("contact=#1 | Annie Easley | due=2026-04-09 | reason=Schedule coffee.", rendered)
            self.assertIn("contact=#2 | Mary Jackson | due=2026-04-14 | reason=Still in window.", rendered)
            self.assertNotIn("due=2026-04-15", rendered)

    def test_today_command_excludes_completed_followups(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            db_path = tmp_path / "networking.db"
            schema_path = ROOT / "config" / "schema.sql"
            initialize_database(db_path=db_path, schema_path=schema_path)
            main(["add-contact", "--name", "Edsger Dijkstra"], db_path=db_path)
            main(
                [
                    "add-followup",
                    "--contact-id",
                    "1",
                    "--due-on",
                    "2026-04-06",
                    "--reason",
                    "Should disappear.",
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
                    "Still pending.",
                ],
                db_path=db_path,
            )
            main(["complete-followup", "--id", "1"], db_path=db_path)

            today_output = StringIO()
            with patch("networking_crm.main.date") as mock_date:
                mock_date.today.return_value = real_date(2026, 4, 7)
                with redirect_stdout(today_output):
                    exit_code = main(["today"], db_path=db_path)

            rendered = today_output.getvalue()
            self.assertEqual(exit_code, 0)
            self.assertIn("Pending follow-ups: 1", rendered)
            self.assertNotIn("Should disappear.", rendered)
            self.assertIn("Still pending.", rendered)

    def test_today_command_empty_state_is_clean(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            db_path = tmp_path / "networking.db"
            schema_path = ROOT / "config" / "schema.sql"
            initialize_database(db_path=db_path, schema_path=schema_path)

            today_output = StringIO()
            with patch("networking_crm.main.date") as mock_date:
                mock_date.today.return_value = real_date(2026, 4, 7)
                with redirect_stdout(today_output):
                    exit_code = main(["today"], db_path=db_path)

            rendered = today_output.getvalue()
            self.assertEqual(exit_code, 0)
            self.assertIn("Pending follow-ups: 0", rendered)
            self.assertIn("Overdue\n  none", rendered)
            self.assertIn("Due Today\n  none", rendered)
            self.assertIn("Upcoming (Next 7 Days)\n  none", rendered)

    def test_complete_followup_marks_status_and_completed_at(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            db_path = tmp_path / "networking.db"
            schema_path = ROOT / "config" / "schema.sql"
            initialize_database(db_path=db_path, schema_path=schema_path)
            main(["add-contact", "--name", "Barbara Liskov"], db_path=db_path)
            main(
                [
                    "add-followup",
                    "--contact-id",
                    "1",
                    "--due-on",
                    "2026-04-10",
                    "--reason",
                    "Send follow-up note.",
                ],
                db_path=db_path,
            )

            complete_output = StringIO()
            with redirect_stdout(complete_output):
                exit_code = main(["complete-followup", "--id", "1"], db_path=db_path)

            self.assertEqual(exit_code, 0)
            self.assertIn("Completed follow-up #1", complete_output.getvalue())

            with get_connection(db_path) as connection:
                followup = connection.execute(
                    """
                    select status, completed_at, due_on, reason
                    from follow_ups
                    where id = 1
                    """
                ).fetchone()

            self.assertEqual(followup["status"], "completed")
            self.assertIsNotNone(followup["completed_at"])
            self.assertEqual(followup["due_on"], "2026-04-10")
            self.assertEqual(followup["reason"], "Send follow-up note.")

    def test_complete_followup_rejects_unknown_followup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            db_path = tmp_path / "networking.db"
            schema_path = ROOT / "config" / "schema.sql"
            initialize_database(db_path=db_path, schema_path=schema_path)

            complete_output = StringIO()
            with redirect_stdout(complete_output):
                exit_code = main(["complete-followup", "--id", "999"], db_path=db_path)

            self.assertEqual(exit_code, 1)
            self.assertIn("Follow-up #999 does not exist.", complete_output.getvalue())

    def test_show_contact_displays_notes_and_followups_with_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            db_path = tmp_path / "networking.db"
            schema_path = ROOT / "config" / "schema.sql"
            initialize_database(db_path=db_path, schema_path=schema_path)
            main(
                [
                    "add-contact",
                    "--name",
                    "Radia Perlman",
                    "--company",
                    "Sun Microsystems",
                    "--role",
                    "Engineer",
                    "--email",
                    "radia@example.com",
                ],
                db_path=db_path,
            )
            main(
                ["add-note", "--contact-id", "1", "--body", "Discussed distributed systems."],
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
                    "Send reading list.",
                ],
                db_path=db_path,
            )
            main(
                [
                    "add-followup",
                    "--contact-id",
                    "1",
                    "--due-on",
                    "2026-04-09",
                    "--reason",
                    "Check in after intro.",
                ],
                db_path=db_path,
            )
            main(["complete-followup", "--id", "2"], db_path=db_path)

            show_output = StringIO()
            with redirect_stdout(show_output):
                exit_code = main(["show-contact", "--id", "1"], db_path=db_path)

            rendered = show_output.getvalue()
            self.assertEqual(exit_code, 0)
            self.assertIn("Contact #1: Radia Perlman", rendered)
            self.assertIn("  Company: Sun Microsystems", rendered)
            self.assertIn("  Role: Engineer", rendered)
            self.assertIn("  Email: radia@example.com", rendered)
            self.assertIn("Notes:", rendered)
            self.assertIn("Discussed distributed systems.", rendered)
            self.assertIn("Follow-ups:", rendered)
            self.assertIn("  - #1 due=2026-04-08 status=pending", rendered)
            self.assertIn("  - #2 due=2026-04-09 status=completed", rendered)
            self.assertIn("    completed_at: ", rendered)

    def test_ari_today_delegates_to_existing_today_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            db_path = tmp_path / "networking.db"
            schema_path = ROOT / "config" / "schema.sql"
            initialize_database(db_path=db_path, schema_path=schema_path)
            main(["add-contact", "--name", "Annie Easley"], db_path=db_path)
            main(
                [
                    "add-followup",
                    "--contact-id",
                    "1",
                    "--due-on",
                    "2026-04-07",
                    "--reason",
                    "Reply today.",
                ],
                db_path=db_path,
            )

            output = StringIO()
            with patch("networking_crm.main.date") as mock_date:
                mock_date.today.return_value = real_date(2026, 4, 7)
                with redirect_stdout(output):
                    exit_code = ari_main(["today"], db_path=db_path)

            rendered = output.getvalue()
            self.assertEqual(exit_code, 0)
            self.assertIn("Today", rendered)
            self.assertIn("Reply today.", rendered)

    def test_ari_contacts_list_delegates_to_existing_list_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            db_path = tmp_path / "networking.db"
            schema_path = ROOT / "config" / "schema.sql"
            initialize_database(db_path=db_path, schema_path=schema_path)
            main(["add-contact", "--name", "Ada Lovelace"], db_path=db_path)

            output = StringIO()
            with redirect_stdout(output):
                exit_code = ari_main(["contacts", "list"], db_path=db_path)

            rendered = output.getvalue()
            self.assertEqual(exit_code, 0)
            self.assertIn("#1 | Ada Lovelace", rendered)

    def test_ari_contacts_show_delegates_to_existing_show_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            db_path = tmp_path / "networking.db"
            schema_path = ROOT / "config" / "schema.sql"
            initialize_database(db_path=db_path, schema_path=schema_path)
            main(["add-contact", "--name", "Grace Hopper"], db_path=db_path)
            main(
                ["add-note", "--contact-id", "1", "--body", "Met at systems meetup."],
                db_path=db_path,
            )

            output = StringIO()
            with redirect_stdout(output):
                exit_code = ari_main(["contacts", "show", "--id", "1"], db_path=db_path)

            rendered = output.getvalue()
            self.assertEqual(exit_code, 0)
            self.assertIn("Contact #1: Grace Hopper", rendered)
            self.assertIn("Met at systems meetup.", rendered)

    def test_ari_followups_due_delegates_to_existing_due_behavior(self) -> None:
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
                    "2026-04-07",
                    "--reason",
                    "Due today.",
                ],
                db_path=db_path,
            )

            output = StringIO()
            with patch("networking_crm.main.date") as mock_date:
                mock_date.today.return_value.isoformat.return_value = "2026-04-07"
                with redirect_stdout(output):
                    exit_code = ari_main(["followups", "due"], db_path=db_path)

            rendered = output.getvalue()
            self.assertEqual(exit_code, 0)
            self.assertIn("#1 | contact=#1 | Margaret Hamilton | due=2026-04-07", rendered)


if __name__ == "__main__":
    unittest.main()
