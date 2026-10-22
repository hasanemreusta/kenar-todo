import unittest

from todo.autostart import startup_command


class AutostartTests(unittest.TestCase):
    def test_command_line(self):
        cmd = startup_command(pythonw=r"C:\Py\pythonw.exe", project=r"C:\Apps\todo-app")
        self.assertTrue(cmd.startswith('"C:\\Py\\pythonw.exe" -c "'))
        self.assertIn(r"sys.path.insert(0, r'C:\Apps\todo-app')", cmd)
        self.assertIn("from todo.gui import main", cmd)

    def test_packaged_detection(self):
        import sys
        from unittest import mock
        from todo.autostart import is_packaged
        with mock.patch.object(sys, "executable", "C:/x/WindowsApps/Pkg_1.0/Todo.exe".replace("/", chr(92))):
            self.assertTrue(is_packaged())
        with mock.patch.object(sys, "executable", "C:/Python311/python.exe".replace("/", chr(92))):
            self.assertFalse(is_packaged())


if __name__ == "__main__":
    unittest.main()
