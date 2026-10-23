"""Offline checks for vet_repos.py. Run: python3 -m unittest scripts/test_vet_repos.py"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from vet_repos import classify_license, parse_repo, sort_key  # noqa: E402


class ParseRepoTest(unittest.TestCase):
    def test_forms(self):
        self.assertEqual(parse_repo("jd/tenacity"), "jd/tenacity")
        self.assertEqual(parse_repo("https://github.com/jd/tenacity"), "jd/tenacity")
        self.assertEqual(parse_repo("github.com/jd/tenacity.git"), "jd/tenacity")
        self.assertEqual(parse_repo("https://github.com/jd/tenacity/blob/main/tenacity/wait.py"), "jd/tenacity")

    def test_rejects(self):
        self.assertIsNone(parse_repo("tenacity"))
        self.assertIsNone(parse_repo("https://gitlab.com/a/b"))


class ClassifyLicenseTest(unittest.TestCase):
    def test_classes(self):
        self.assertEqual(classify_license("MIT"), "permissive")
        self.assertEqual(classify_license("Apache-2.0"), "permissive")
        self.assertEqual(classify_license("GPL-3.0"), "copyleft")
        self.assertEqual(classify_license("AGPL-3.0-only"), "copyleft")
        self.assertEqual(classify_license("LGPL-2.1"), "weak-copyleft")
        self.assertEqual(classify_license("MPL-2.0"), "weak-copyleft")
        self.assertEqual(classify_license(""), "none")
        self.assertEqual(classify_license(None), "none")
        self.assertEqual(classify_license("NOASSERTION"), "unknown")

    def test_dual_license_picks_permissive_option(self):
        self.assertEqual(classify_license("MIT OR GPL-2.0"), "permissive")
        self.assertEqual(classify_license("MIT AND GPL-2.0"), "copyleft")


class SortTest(unittest.TestCase):
    def test_ok_before_ask_before_avoid_then_maintained_then_stars(self):
        rows = [
            {"verdict": "avoid", "maintained": 10, "stars": 9999},
            {"verdict": "ok", "maintained": 3, "stars": 9999},
            {"verdict": "ok", "maintained": 10, "stars": 10},
            {"verdict": "ask-user", "maintained": None, "stars": None},
        ]
        ordered = sorted(rows, key=sort_key)
        self.assertEqual([(r["verdict"], r["maintained"]) for r in ordered],
                         [("ok", 10), ("ok", 3), ("ask-user", None), ("avoid", 10)])


if __name__ == "__main__":
    unittest.main()
