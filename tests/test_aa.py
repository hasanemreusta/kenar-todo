import unittest

from todo.aa import rounded_rect_rows


class RoundedRectTests(unittest.TestCase):
    def setUp(self):
        self.rows = rounded_rect_rows(40, 30, 10, fill="#0c0c0e", border="#ffffff", bg="#010203")

    def test_size(self):
        self.assertEqual(len(self.rows), 30)
        self.assertTrue(all(len(r) == 40 for r in self.rows))

    def test_corner_is_background_and_center_is_fill(self):
        self.assertEqual(self.rows[0][0], "#010203")
        self.assertEqual(self.rows[15][20], "#0c0c0e")

    def test_edge_is_smoothed(self):
        # a pixel on the rounded corner is neither pure background nor pure fill/border
        corner = [self.rows[y][x] for y in range(0, 6) for x in range(0, 6)]
        self.assertTrue(any(c not in ("#010203", "#0c0c0e", "#ffffff") for c in corner))

    def test_border_is_drawn_on_straight_edge(self):
        self.assertNotEqual(self.rows[15][0], "#010203")
        self.assertNotEqual(self.rows[15][0], "#0c0c0e")

    def test_circle_without_border(self):
        rows = rounded_rect_rows(20, 20, 10, fill="#34d27b", bg="#000000")
        self.assertEqual(rows[10][10], "#34d27b")
        self.assertEqual(rows[0][0], "#000000")


if __name__ == "__main__":
    unittest.main()
