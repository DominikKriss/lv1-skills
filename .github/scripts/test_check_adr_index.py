import tempfile
import unittest
from pathlib import Path

import check_adr_index as c

ADR = "# 0001. First\n\n- **Status:** Accepted\n- **Scope:** all\n- **Date:** 2026-11-21\n"
ROW = "| [0001](0001-first.md) | First | Accepted | all | 2026-11-21 |\n"
HEAD = "| # | Title | Status | Scope | Date |\n|---|---|---|---|---|\n"


def errors(files):
    with tempfile.TemporaryDirectory() as d:
        for name, text in files.items():
            Path(d, name).write_text(text)
        return c.check(Path(d))


class Index(unittest.TestCase):
    def test_matching_index_ok(self):
        self.assertEqual(errors({"0001-first.md": ADR, "README.md": HEAD + ROW}), [])

    def test_missing_row(self):
        self.assertIn("index: 0001-first.md is not listed", errors({"0001-first.md": ADR, "README.md": HEAD}))

    def test_status_mismatch(self):
        e = errors({"0001-first.md": ADR, "README.md": HEAD + ROW.replace("Accepted", "Proposed")})
        self.assertTrue(any("status" in x for x in e), e)

    def test_row_without_file(self):
        self.assertIn("index: 0001 has no ADR file", errors({"README.md": HEAD + ROW}))

    def test_bad_status_word(self):
        e = errors({"0001-first.md": ADR.replace("Accepted", "Done"),
                    "README.md": HEAD + ROW.replace("Accepted", "Done")})
        self.assertTrue(any("is not Proposed" in x for x in e), e)

    def test_superseded_ok(self):
        sup = ADR.replace("Accepted", "Superseded by 0002")
        self.assertEqual(errors({"0001-first.md": sup,
                                 "README.md": HEAD + ROW.replace("Accepted", "Superseded by 0002")}), [])

    def test_duplicate_number_refused(self):
        second = ADR.replace("First", "Second")
        e = errors({"0001-first.md": ADR, "0001-second.md": second,
                    "README.md": HEAD + "| [0001](0001-second.md) | Second | Accepted | all | 2026-11-21 |\n"})
        self.assertTrue(any("already used" in x for x in e), e)

    def test_distinct_numbers_ok(self):
        second = ADR.replace("0001. First", "0002. Second")
        row2 = "| [0002](0002-second.md) | Second | Accepted | all | 2026-11-21 |\n"
        self.assertEqual(errors({"0001-first.md": ADR, "0002-second.md": second, "README.md": HEAD + ROW + row2}), [])

    def test_real_index(self):
        self.assertEqual(c.check(Path(__file__).resolve().parents[2] / "docs" / "adr"), [])


if __name__ == "__main__":
    unittest.main()
