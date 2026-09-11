import json
import tempfile
import unittest
from pathlib import Path

from redirectproof.check import check


class RedirectTests(unittest.TestCase):
    def test_cycle(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "_redirects"
            path.write_text("/a /b 301\n/b /a 301\n")
            self.assertIn("RP105", {item.rule for item in check(path)})

    def test_shadowed_rule(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "_redirects"
            path.write_text("/* /index.html 200\n/old /new 301\n")
            rules = {item.rule for item in check(path)}
            self.assertIn("RP104", rules)

    def test_invalid_status(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "_redirects"
            path.write_text("/old /new 201\n")
            self.assertEqual("RP101", check(path)[0].rule)

    def test_valid_vercel(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "vercel.json"
            path.write_text(json.dumps({"redirects": [{"source": "/old", "destination": "/new", "permanent": True}]}))
            self.assertEqual([], check(path))


if __name__ == "__main__":
    unittest.main()
