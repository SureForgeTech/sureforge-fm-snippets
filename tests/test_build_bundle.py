#!/usr/bin/env python3
"""
tests/test_build_bundle.py

Unit tests for tools/build-bundle.py script and Alfred snippets parity checks.
"""

import csv
import io
import json
import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

# Add repo root to sys.path so tools can be imported
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import importlib.util

spec = importlib.util.spec_from_file_location("build_bundle", REPO_ROOT / "tools" / "build-bundle.py")
build_bundle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_bundle)

lint_row = build_bundle.lint_row
load_existing_uids = build_bundle.load_existing_uids
build_snippet_json = build_bundle.build_snippet_json
get_snippet_filename = build_bundle.get_snippet_filename


class TestBuildBundle(unittest.TestCase):
    def test_lint_row_valid(self):
        row = {
            "Name": "Abs",
            "Keyword": ";fmabs",
            "Snippet": "Abs ( number )",
            "Category": "Numeric",
        }
        seen = set()
        errors = lint_row(1, row, seen)
        self.assertEqual(errors, [])
        self.assertIn(";fmabs", seen)

    def test_lint_row_missing_fields(self):
        seen = set()
        errors = lint_row(1, {"Name": "", "Keyword": "", "Snippet": "", "Category": ""}, seen)
        self.assertEqual(len(errors), 4)

    def test_lint_row_invalid_prefix(self):
        seen = set()
        errors = lint_row(1, {"Name": "Abs", "Keyword": "abs", "Snippet": "x", "Category": "Num"}, seen)
        self.assertTrue(any("must start with ';fm'" in e for e in errors))

    def test_lint_row_uppercase_keyword(self):
        seen = set()
        errors = lint_row(1, {"Name": "Abs", "Keyword": ";fmABS", "Snippet": "x", "Category": "Num"}, seen)
        self.assertTrue(any("must be all lowercase" in e for e in errors))

    def test_lint_row_duplicate_keyword(self):
        seen = {";fmabs"}
        errors = lint_row(1, {"Name": "Abs", "Keyword": ";fmabs", "Snippet": "x", "Category": "Num"}, seen)
        self.assertTrue(any("Duplicate keyword" in e for e in errors))

    def test_build_snippet_json_structure(self):
        json_str = build_snippet_json("Abs", ";fmabs", "Abs ( number )", "UUID-123")
        data = json.loads(json_str)
        self.assertIn("alfredsnippet", data)
        self.assertEqual(data["alfredsnippet"]["name"], "Abs")
        self.assertEqual(data["alfredsnippet"]["keyword"], ";fmabs")
        self.assertEqual(data["alfredsnippet"]["snippet"], "Abs ( number )")
        self.assertEqual(data["alfredsnippet"]["uid"], "UUID-123")

    def test_get_snippet_filename(self):
        fname = get_snippet_filename("Get Field Value", "UUID-123")
        self.assertEqual(fname, "Get_Field_Value [UUID-123].json")

    def test_load_existing_uids_and_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle_path = Path(tmpdir) / "test.alfredsnippets"
            with zipfile.ZipFile(bundle_path, "w") as zf:
                payload = build_snippet_json("Abs", ";fmabs", "Abs ( number )", "EXISTING-UID")
                zf.writestr("Abs [EXISTING-UID].json", payload)

            uids = load_existing_uids(bundle_path)
            self.assertEqual(uids.get(";fmabs"), "EXISTING-UID")

    def test_load_existing_uids_malformed_member_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle_path = Path(tmpdir) / "corrupt.alfredsnippets"
            with zipfile.ZipFile(bundle_path, "w") as zf:
                zf.writestr("corrupt [1].json", "NOT VALID JSON {")
                payload = build_snippet_json("Valid", ";fmvalid", "Valid ()", "VALID-UID")
                zf.writestr("Valid [VALID-UID].json", payload)

            with self.assertRaises(RuntimeError):
                load_existing_uids(bundle_path)

    def test_lint_row_unquoted_comma_surplus_fields(self):
        seen = set()
        # DictReader puts surplus fields under None key when there are unquoted commas
        row = {
            "Name": "Abs",
            "Keyword": ";fmabs",
            "Snippet": "Abs ( a",
            "Category": "Numeric",
            None: ["b )"],
        }
        errors = lint_row(1, row, seen)
        self.assertTrue(any("Surplus fields detected" in e for e in errors))

    def test_lint_row_correctly_quoted_comma(self):
        seen = set()
        row = {
            "Name": "Abs",
            "Keyword": ";fmabs",
            "Snippet": "Abs ( a ; b )",
            "Category": "Numeric",
        }
        errors = lint_row(1, row, seen)
        self.assertEqual(errors, [])

    def test_csv_strict_parsing_malformed_quote(self):
        import subprocess
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_csv = Path(tmpdir) / "bad.csv"
            bad_csv.write_text('Name,Keyword,Snippet,Category\nAbs,;fmabs,"Abs ( number )"oops,Numeric\n', encoding="utf-8")
            cmd = [sys.executable, str(REPO_ROOT / "tools" / "build-bundle.py"), "--csv", str(bad_csv)]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("CSV format error", result.stderr)

    def test_csv_missing_header_fails(self):
        import subprocess
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_csv = Path(tmpdir) / "missing_header.csv"
            bad_csv.write_text("Name,Keyword\nAbs,;fmabs\n", encoding="utf-8")
            cmd = [sys.executable, str(REPO_ROOT / "tools" / "build-bundle.py"), "--csv", str(bad_csv)]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing required columns", result.stderr)

    def test_csv_empty_file_fails(self):
        import subprocess
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_csv = Path(tmpdir) / "empty.csv"
            bad_csv.write_text("Name,Keyword,Snippet,Category\n", encoding="utf-8")
            cmd = [sys.executable, str(REPO_ROOT / "tools" / "build-bundle.py"), "--csv", str(bad_csv)]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("no snippet rows", result.stderr)

    def test_embedded_newlines_preserved(self):
        import subprocess
        with tempfile.TemporaryDirectory() as tmpdir:
            test_csv = Path(tmpdir) / "multiline.csv"
            test_bundle = Path(tmpdir) / "out.alfredsnippets"
            snippet_content = "Line1\nLine2\r\nLine3"
            test_csv.write_bytes(f'Name,Keyword,Snippet,Category\nTest,;fmtest,"{snippet_content}",General\n'.encode("utf-8"))
            cmd = [sys.executable, str(REPO_ROOT / "tools" / "build-bundle.py"), "--csv", str(test_csv), "--bundle", str(test_bundle)]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
            self.assertEqual(result.returncode, 0, result.stderr)

            # Check inside zip that newline content was preserved
            with zipfile.ZipFile(test_bundle, "r") as zf:
                fname = [n for n in zf.namelist() if n.startswith("Test")][0]
                data = json.loads(zf.read(fname).decode("utf-8"))
                self.assertEqual(data["alfredsnippet"]["snippet"], snippet_content)

    def test_repo_bundle_parity(self):
        """Verify the actual repository CSV and bundle pass parity check."""
        cmd = [sys.executable, str(REPO_ROOT / "tools" / "build-bundle.py"), "--check"]
        import subprocess
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
        self.assertEqual(result.returncode, 0, f"Parity check failed:\n{result.stderr}")
        self.assertIn("Parity check passed", result.stdout)


if __name__ == "__main__":
    unittest.main()
