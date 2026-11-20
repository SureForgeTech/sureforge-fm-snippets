#!/usr/bin/env python3
"""
tools/build-bundle.py

Generates and validates the Alfred snippets bundle (FileMaker_Functions.alfredsnippets)
from the source CSV file (data/FileMaker_Functions_Alfred_Snippets.csv).

Preserves existing UIDs for unchanged keywords so Alfred snippet collections
update in place without duplicates.
"""

import argparse
import csv
import json
import os
import sys
import uuid
import zipfile
from pathlib import Path

REQUIRED_HEADERS = {"Name", "Keyword", "Snippet", "Category"}


def lint_row(idx: int, row: dict, seen_keywords: set) -> list[str]:
    """Validate a single CSV row according to CONTRIBUTING.md guidelines."""
    errors = []

    # Check for surplus fields (e.g. unquoted comma in snippet)
    if None in row:
        errors.append(f"Row {idx}: Surplus fields detected (possible unquoted comma): {row[None]}")

    # Check for missing fields
    missing_headers = [h for h in REQUIRED_HEADERS if h not in row or row[h] is None]
    if missing_headers:
        errors.append(f"Row {idx}: Missing fields for headers {missing_headers}")

    name = (row.get("Name") or "").strip()
    kw = (row.get("Keyword") or "").strip()
    snippet = row.get("Snippet") or ""
    category = (row.get("Category") or "").strip()

    if not name:
        errors.append(f"Row {idx}: Name is empty")
    if not category:
        errors.append(f"Row {idx}: Category is empty")
    if not snippet:
        errors.append(f"Row {idx}: Snippet is empty for '{name}'")

    if not kw:
        errors.append(f"Row {idx}: Keyword is empty for '{name}'")
    else:
        if not kw.startswith(";fm"):
            errors.append(f"Row {idx}: Keyword '{kw}' must start with ';fm'")
        if kw != kw.lower():
            errors.append(f"Row {idx}: Keyword '{kw}' must be all lowercase")
        if kw in seen_keywords:
            errors.append(f"Row {idx}: Duplicate keyword '{kw}' found")
        seen_keywords.add(kw)

    return errors


def load_existing_uids(bundle_path: Path) -> dict[str, str]:
    """Extract existing keyword -> uid mappings from an existing .alfredsnippets zip.

    Raises RuntimeError if the bundle exists but cannot be read or contains malformed JSON,
    preventing partial UID loads that would overwrite existing UIDs on regeneration.
    """
    if not bundle_path.is_file():
        return {}
    uid_map = {}
    with zipfile.ZipFile(bundle_path, "r") as zf:
        for name in zf.namelist():
            if name.endswith(".json"):
                try:
                    data = json.loads(zf.read(name).decode("utf-8"))
                    snippet_data = data.get("alfredsnippet", {})
                    kw = snippet_data.get("keyword")
                    uid = snippet_data.get("uid")
                    if not kw or not uid:
                        raise ValueError(f"Missing keyword or uid in {name}")
                    uid_map[kw] = uid
                except Exception as e:
                    raise RuntimeError(f"Corrupt or unparseable snippet '{name}' in {bundle_path.name}: {e}") from e
    return uid_map


def build_snippet_json(name: str, kw: str, snippet: str, uid: str) -> str:
    """Generate formatting-exact Alfred snippet JSON matching existing format."""
    payload = {
        "alfredsnippet": {
            "snippet": snippet,
            "uid": uid,
            "name": name,
            "keyword": kw,
        }
    }
    return json.dumps(payload, indent=2) + "\n"


def get_snippet_filename(name: str, uid: str) -> str:
    """Standard Alfred snippet filename inside zip."""
    safe_name = name.replace(" ", "_")
    return f"{safe_name} [{uid}].json"


def main():
    parser = argparse.ArgumentParser(description="Build or verify FileMaker Alfred snippets bundle.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check parity between CSV and .alfredsnippets bundle without modifying files.",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("data/FileMaker_Functions_Alfred_Snippets.csv"),
        help="Path to source CSV file.",
    )
    parser.add_argument(
        "--bundle",
        type=Path,
        default=Path("FileMaker_Functions.alfredsnippets"),
        help="Path to output .alfredsnippets bundle.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    csv_path = repo_root / args.csv
    bundle_path = repo_root / args.bundle

    if not csv_path.is_file():
        print(f"Error: CSV file not found at {csv_path}", file=sys.stderr)
        sys.exit(1)

    # 1. Parse and validate CSV with strict parsing
    rows = []
    seen_keywords = set()
    lint_errors = []

    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, strict=True)
        if not reader.fieldnames or not REQUIRED_HEADERS.issubset(set(reader.fieldnames)):
            lint_errors.append(f"CSV header missing required columns: {REQUIRED_HEADERS - set(reader.fieldnames or [])}")
        idx = 2
        while True:
            try:
                row = next(reader)
            except StopIteration:
                break
            except csv.Error as e:
                lint_errors.append(f"Row {idx}: CSV format error: {e}")
                break
            errs = lint_row(idx, row, seen_keywords)
            lint_errors.extend(errs)
            rows.append(row)
            idx += 1

    if not rows and not lint_errors:
        lint_errors.append("CSV file contains no snippet rows")

    if lint_errors:
        print("Linting errors in CSV:", file=sys.stderr)
        for err in lint_errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(1)

    try:
        existing_uids = load_existing_uids(bundle_path)
    except RuntimeError as e:
        print(f"Error loading bundle: {e}", file=sys.stderr)
        sys.exit(1)

    # 2. Build expected entries
    expected_entries = {}
    for row in rows:
        name = row["Name"].strip()
        kw = row["Keyword"].strip()
        snippet = row["Snippet"]
        uid = existing_uids.get(kw, str(uuid.uuid4()).upper())
        fname = get_snippet_filename(name, uid)
        json_content = build_snippet_json(name, kw, snippet, uid)
        expected_entries[fname] = (kw, uid, name, snippet, json_content)

    # 3. Check mode
    if args.check:
        if not bundle_path.is_file():
            print(f"Error: Bundle file not found at {bundle_path}", file=sys.stderr)
            sys.exit(1)

        discrepancies = []
        with zipfile.ZipFile(bundle_path, "r") as zf:
            existing_files = set(zf.namelist())
            expected_files = set(expected_entries.keys())

            missing_in_bundle = expected_files - existing_files
            extra_in_bundle = existing_files - expected_files

            if missing_in_bundle:
                discrepancies.append(f"Missing from bundle ({len(missing_in_bundle)} items): {list(missing_in_bundle)[:5]}")
            if extra_in_bundle:
                discrepancies.append(f"Extra in bundle ({len(extra_in_bundle)} items): {list(extra_in_bundle)[:5]}")

            for fname in expected_files.intersection(existing_files):
                bundle_data = zf.read(fname).decode("utf-8")
                expected_data = expected_entries[fname][4]
                try:
                    b_obj = json.loads(bundle_data)["alfredsnippet"]
                    e_obj = json.loads(expected_data)["alfredsnippet"]
                    if b_obj != e_obj:
                        discrepancies.append(f"Content mismatch in {fname}: bundle has {b_obj}, expected {e_obj}")
                except Exception as e:
                    discrepancies.append(f"Failed to parse {fname}: {e}")

        if discrepancies:
            print("Parity check FAILED: bundle and CSV are out of sync:", file=sys.stderr)
            for d in discrepancies:
                print(f"  - {d}", file=sys.stderr)
            sys.exit(1)

        print(f"Parity check passed: all {len(rows)} snippets match between CSV and bundle.")
        sys.exit(0)

    # 4. Write bundle atomically via temporary file
    # Write deterministically sorted by filename
    tmp_bundle = bundle_path.with_suffix(".tmp")
    with zipfile.ZipFile(tmp_bundle, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for fname in sorted(expected_entries.keys()):
            content = expected_entries[fname][4]
            # Use fixed timestamp for reproducible builds
            zinfo = zipfile.ZipInfo(fname, date_time=(2026, 1, 1, 0, 0, 0))
            zinfo.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(zinfo, content.encode("utf-8"))
    tmp_bundle.replace(bundle_path)

    print(f"Successfully generated {bundle_path.name} with {len(rows)} snippets.")


if __name__ == "__main__":
    main()
