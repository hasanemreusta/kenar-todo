import unittest
from todo.weekday import next_weekday

class TestWeekday(unittest.TestCase):
    def test_weekday(self):
        self.assertEqual(next_weekday("cuma", "2026-10-21"), "2026-10-23")
        self.assertEqual(next_weekday("pazartesi", "2026-10-21"), "2026-10-26")
        self.assertEqual(next_weekday("carsamba", "2026-10-21"), "2026-10-28")
        self.assertEqual(next_weekday("\u00e7ar\u015famba", "2026-10-21"), "2026-10-28")
        self.assertEqual(next_weekday("pazar", "2026-10-21"), "2026-10-25")
        self.assertEqual(next_weekday("Sal\u0131", "2026-10-21"), "2026-10-27")
        self.assertIsNone(next_weekday("kedi", "2026-10-21"))

if __name__ == '__main__':
    unittest.main()
