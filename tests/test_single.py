import subprocess
import sys
import unittest
import uuid

from todo.single import acquire


class SingleInstanceTests(unittest.TestCase):
    def test_second_acquire_in_same_process_fails(self):
        name = "TodoAppTest" + uuid.uuid4().hex
        self.assertTrue(acquire(name))
        self.assertFalse(acquire(name))

    @unittest.skipUnless(sys.platform == "win32", "named mutex is Windows only")
    def test_other_process_cannot_acquire(self):
        name = "TodoAppTest" + uuid.uuid4().hex
        self.assertTrue(acquire(name))
        code = "import sys; from todo.single import acquire; sys.exit(0 if acquire(%r) else 3)" % name
        result = subprocess.run([sys.executable, "-c", code], capture_output=True)
        self.assertEqual(result.returncode, 3)


if __name__ == "__main__":
    unittest.main()
