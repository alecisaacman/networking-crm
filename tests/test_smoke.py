import sys
import tempfile
import unittest
from pathlib import Path
from io import StringIO
from contextlib import redirect_stdout


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


if __name__ == "__main__":
    unittest.main()
