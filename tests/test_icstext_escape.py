import unittest

from todo.icstext import ics_escape

BS = chr(92)   # a single backslash


class EscapeTests(unittest.TestCase):
    def test_plain_and_empty(self):
        self.assertEqual(ics_escape("plain text"), "plain text")
        self.assertEqual(ics_escape(""), "")

    def test_specials(self):
        self.assertEqual(ics_escape("a,b;c"), "a" + BS + "," + "b" + BS + ";" + "c")
        self.assertEqual(ics_escape("a" + BS + "b"), "a" + BS + BS + "b")

    def test_newlines(self):
        self.assertEqual(ics_escape("line1\nline2"), "line1" + BS + "nline2")
        self.assertEqual(ics_escape("a\r\nb"), "a" + BS + "nb")
        self.assertEqual(ics_escape("a\rb"), "a" + BS + "nb")


if __name__ == "__main__":
    unittest.main()
