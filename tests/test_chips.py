import unittest
from todo.chips import due_chip

class TestDueChip(unittest.TestCase):
    def test_overdue_3_days(self):
        self.assertEqual(due_chip("2023-01-01", "2023-01-04"), ("3 g\u00fcn ge\u00e7ti", "overdue"))

    def test_yesterday(self):
        self.assertEqual(due_chip("2023-01-02", "2023-01-03"), ("D\u00fcn", "overdue"))

    def test_today(self):
        self.assertEqual(due_chip("2023-01-03", "2023-01-03"), ("Bug\u00fcn", "today"))

    def test_tomorrow(self):
        self.assertEqual(due_chip("2023-01-04", "2023-01-03"), ("Yar\u0131n", "soon"))

    def test_in_4_days(self):
        self.assertEqual(due_chip("2023-01-07", "2023-01-03"), ("4 g\u00fcn kald\u0131", "soon"))

    def test_in_10_days(self):
        self.assertEqual(due_chip("2023-03-05", "2023-01-31"), ("5 Mar", "later"))
        self.assertEqual(due_chip("2023-02-10", "2023-01-31"), ("10 \u015eub", "later"))

if __name__ == "__main__":
    unittest.main()
