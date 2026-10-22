import unittest


class GuiImportTest(unittest.TestCase):
    def test_import(self):
        import todo.gui  # noqa: F401


if __name__ == "__main__":
    unittest.main()

