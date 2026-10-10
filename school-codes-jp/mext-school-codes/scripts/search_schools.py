#!/usr/bin/env python3
"""Read-only CLI search for MEXT school CSV using approved Unicode aliases.

Example:
 python3 scripts/search_schools.py data/schools.csv '高崎' --limit 20
"""
import argparse
import csv
import json
from pathlib import Path

try:
    from scripts.search_normalization import matches_search, normalize_search
except ModuleNotFoundError:
    from search_normalization import matches_search, normalize_search

NAME_FIELDS = ("school_name", "学校名")
ADDRESS_FIELDS = ("address", "school_address", "学校所在地")
CODE_FIELDS = ("school_code", "学校コード")


def choose_field(headers, choices, description):
    for name in choices:
        if name in headers:
            return name
    raise ValueError(f"Missing {description} field; available headers: {headers}")


def search_csv(path, query, limit=20):
    if not query:
        raise ValueError("Search query cannot be empty")
    if limit < 1:
        raise ValueError("Limit must be positive")
    results = []
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        headers = reader.fieldnames or []
        name_field = choose_field(headers, NAME_FIELDS, "school name")
        address_field = next((h for h in ADDRESS_FIELDS if h in headers), None)
        code_field = choose_field(headers, CODE_FIELDS, "school code")
        for row in reader:
            name = row.get(name_field) or ""
            address = row.get(address_field) or "" if address_field else ""
            if not (matches_search(query, name) or matches_search(query, address)):
                continue
            exact = query in name or query in address
            results.append({
                "school_code": row.get(code_field),
                "school_name": name,
                "address": address,
                "match_type": "exact" if exact else "character_variant",
            })
    results.sort(key=lambda r: (r["match_type"] != "exact", r["school_code"] or ""))
    return results[:limit]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path)
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    print(json.dumps(search_csv(args.csv_file, args.query, args.limit), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
