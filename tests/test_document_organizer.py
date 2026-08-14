import json
import tempfile
import unittest
from pathlib import Path

from document_organizer import organize_documents


class DocumentOrganizerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.inbox = self.root / "inbox"
        self.output_parent = self.root / "output"
        self.inbox.mkdir()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_copies_supported_files_and_writes_report(self):
        (self.inbox / "resume.PDF").write_text("pdf", encoding="utf-8")
        (self.inbox / "notes.md").write_text("not supported", encoding="utf-8")

        summary = organize_documents(self.output_parent, [self.inbox])

        self.assertEqual(summary.scanned, 2)
        self.assertEqual(summary.supported, 1)
        self.assertEqual(summary.copied, 1)
        self.assertTrue((self.output_parent / "documents" / "PDF" / "resume.PDF").exists())
        report = self.output_parent / "documents" / "organization_report.json"
        self.assertEqual(json.loads(report.read_text(encoding="utf-8"))["summary"]["copied"], 1)

    def test_collision_gets_numbered_suffix(self):
        source_a = self.inbox / "report.pdf"
        source_b = self.root / "second" / "report.pdf"
        source_a.write_text("first", encoding="utf-8")
        source_b.parent.mkdir()
        source_b.write_text("second", encoding="utf-8")

        summary = organize_documents(self.output_parent, [self.inbox, source_b.parent])

        self.assertEqual(summary.copied, 2)
        pdf_dir = self.output_parent / "documents" / "PDF"
        self.assertEqual(sorted(path.name for path in pdf_dir.glob("*.pdf")), ["report.pdf", "report_1.pdf"])

    def test_dry_run_does_not_create_output(self):
        (self.inbox / "deck.pptx").write_text("slides", encoding="utf-8")

        summary = organize_documents(self.output_parent, [self.inbox], dry_run=True)

        self.assertEqual(summary.copied, 1)
        self.assertFalse(self.output_parent.exists())

    def test_generated_output_is_not_scanned_again(self):
        self.inbox.joinpath("file.txt").write_text("hello", encoding="utf-8")

        summary = organize_documents(self.inbox, [self.inbox])

        self.assertEqual(summary.scanned, 1)
        self.assertEqual(summary.copied, 1)


if __name__ == "__main__":
    unittest.main()
