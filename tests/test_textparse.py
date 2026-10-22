import unittest

from todo.textparse import due_from_text, parse_tags

TODAY = "2026-01-31"


class ParseTagsTests(unittest.TestCase):
    def test_split_and_clean(self):
        self.assertEqual(parse_tags("Ev, #Is  market, ev"), ["ev", "is", "market"])

    def test_empty(self):
        self.assertEqual(parse_tags(""), [])
        self.assertEqual(parse_tags(" , # "), [])


class DueFromTextTests(unittest.TestCase):
    def test_keywords(self):
        self.assertEqual(due_from_text("bugun", TODAY), TODAY)
        self.assertEqual(due_from_text("Bugün", TODAY), TODAY)
        self.assertEqual(due_from_text("yarin", TODAY), "2026-02-01")
        self.assertEqual(due_from_text("yarın", TODAY), "2026-02-01")
        self.assertEqual(due_from_text("haftaya", TODAY), "2026-02-07")

    def test_offset_and_iso(self):
        self.assertEqual(due_from_text("+3", TODAY), "2026-02-03")
        self.assertEqual(due_from_text("2026-03-05", TODAY), "2026-03-05")

    def test_clear(self):
        self.assertIsNone(due_from_text("-", TODAY))
        self.assertIsNone(due_from_text("  ", TODAY))

    def test_invalid(self):
        for bad in ("nonsense", "2026-13-45", "+0", "+x"):
            with self.assertRaises(ValueError):
                due_from_text(bad, TODAY)


if __name__ == "__main__":
    unittest.main()
