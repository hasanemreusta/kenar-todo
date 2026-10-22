import unittest
from todo.quickadd import parse_quick

TODAY = "2026-01-31"


class QuickAddTests(unittest.TestCase):
    def parse(self, text):
        return parse_quick(text, TODAY)

    def test_plain_title(self):
        self.assertEqual(self.parse("S\u00fct al"),
                         {"title": "S\u00fct al", "priority": "medium", "due": None, "tags": []})

    def test_full_line(self):
        r = self.parse("S\u00fct al !high #ev @tomorrow")
        self.assertEqual((r["title"], r["priority"], r["due"], r["tags"]),
                         ("S\u00fct al", "high", "2026-02-01", ["ev"]))

    def test_shortcuts_and_case(self):
        self.assertEqual(self.parse("a !L")["priority"], "low")
        self.assertEqual(self.parse("a !h")["priority"], "high")
        self.assertEqual(self.parse("a !M")["priority"], "medium")

    def test_tags_deduplicated_lowercase(self):
        self.assertEqual(self.parse("a #Ev #ev #is")["tags"], ["ev", "is"])

    def test_lone_hash_stays(self):
        self.assertEqual(self.parse("a # b")["title"], "a # b")

    def test_dates(self):
        self.assertEqual(self.parse("a @today")["due"], TODAY)
        self.assertEqual(self.parse("a @bug\u00fcn")["due"], TODAY)
        self.assertEqual(self.parse("a @yar\u0131n")["due"], "2026-02-01")
        self.assertEqual(self.parse("a @2026-03-05")["due"], "2026-03-05")

    def test_invalid_tokens_stay_in_title(self):
        r = self.parse("a @2026-13-45 !xyz")
        self.assertEqual(r["title"], "a @2026-13-45 !xyz")
        self.assertIsNone(r["due"])
        self.assertEqual(r["priority"], "medium")


if __name__ == "__main__":
    unittest.main()
