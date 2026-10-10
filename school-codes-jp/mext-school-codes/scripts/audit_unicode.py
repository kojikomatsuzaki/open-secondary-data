#!/usr/bin/env python3
"""Read-only Unicode audit of MEXT school records (Python standard library only).

Usage:
    python3 scripts/audit_unicode.py data/schools.csv --output reports/unicode-audit.json

The script NEVER edits source or dataset files. The JSON report is UTF-8.
"""
import argparse
import csv
import json
import sys
import unicodedata
from collections import Counter
from pathlib import Path


def category_of(character):
    code = ord(character)
    if 0xE0100 <= code <= 0xE01EF or 0xFE00 <= code <= 0xFE0F:
        return "variation_selector"
    if 0xE000 <= code <= 0xF8FF or 0xF0000 <= code <= 0xFFFFD or 0x100000 <= code <= 0x10FFFD:
        return "private_use"
    if 0x2F00 <= code <= 0x2FDF:
        return "kangxi_radical"
    if 0x2E80 <= code <= 0x2EFF:
        return "cjk_radicals_supplement"
    if 0xF900 <= code <= 0xFAFF or 0x2F800 <= code <= 0x2FA1F:
        return "cjk_compatibility_ideograph"
    if code in (0x2110, 0x207A, 0x2212):
        return "review_symbol"
    return None


def audit(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("CSV header is missing")
        if len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError("Duplicate CSV headers")
        records = 0
        findings = []
        counts = Counter()
        for row_number, row in enumerate(reader, start=2):
            records += 1
            code = next((row.get(key) for key in ("school_code", "学校コード", "code") if key in row), None)
            for field, value in row.items():
                if value is None:
                    continue
                for offset, character in enumerate(value):
                    kind = category_of(character)
                    if kind is None:
                        continue
                    counts[kind] += 1
                    base = value[offset - 1] if kind == "variation_selector" and offset else None
                    findings.append({
                        "row": row_number, "school_code": code, "field": field,
                        "offset": offset, "character": character,
                        "codepoint": f"U+{ord(character):04X}",
                        "unicode_name": unicodedata.name(character, "UNASSIGNED"),
                        "category": kind,
                        "base_codepoint": f"U+{ord(base):04X}" if base else None,
                        "compatibility_normalized_character": (
                            unicodedata.normalize("NFKC", character)
                            if kind in ("kangxi_radical", "cjk_radicals_supplement") else None
                        ),
                    })
        return {
            "source": str(path), "records": records,
            "unicode_version": unicodedata.unidata_version,
            "counts": dict(sorted(counts.items())), "findings": findings,
            "notes": [
                "This is detection only; no source or derived data was modified.",
                "Variation selector detection does not establish IVD registration.",
                "The scan flags selected suspicious symbols, not every possible Unicode anomaly.",
                "Review contextual meanings before normalizing any character."
            ],
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path)
    parser.add_argument("--output", type=Path, help="Optional report destination")
    args = parser.parse_args()
    report = audit(args.csv_file)
    serialized = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    else:
        print(serialized, end="")
    print(f"Audited {report['records']} records; {len(report['findings'])} findings", file=sys.stderr)


if __name__ == "__main__":
    main()
