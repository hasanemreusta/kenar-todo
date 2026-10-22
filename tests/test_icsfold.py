import unittest

from todo.icsfold import fold_line


def unfold(text):
    return text.replace("\r\n ", "")


class FoldTests(unittest.TestCase):
    def test_short_and_empty(self):
        self.assertEqual(fold_line("SUMMARY:short"), "SUMMARY:short")
        self.assertEqual(fold_line(""), "")
        exact = "x" * 75
        self.assertEqual(fold_line(exact), exact)

    def test_long_ascii(self):
        line = "DESCRIPTION:" + "a" * 200
        folded = fold_line(line)
        pieces = folded.split("\r\n")
        self.assertTrue(all(len(p.encode("utf-8")) <= 75 for p in pieces))
        self.assertTrue(all(p.startswith(" ") for p in pieces[1:]))
        self.assertEqual(len(pieces[0]), 75)
        self.assertEqual(unfold(folded), line)

    def test_multibyte_never_split(self):
        line = "SUMMARY:" + "\u00e9" * 60 + "\u011f\u015f" * 20
        folded = fold_line(line)
        pieces = folded.split("\r\n")
        self.assertGreater(len(pieces), 1)
        self.assertTrue(all(len(p.encode("utf-8")) <= 75 for p in pieces))
        self.assertEqual(unfold(folded), line)


if __name__ == "__main__":
    unittest.main()
