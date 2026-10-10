"""Read-only search integration tests using a synthetic CSV."""
import csv
import tempfile
import unittest
from pathlib import Path

from scripts.search_schools import search_csv


class SearchCsvTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "schools.csv"
        with self.path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["school_code", "school_name", "address"])
            writer.writeheader()
            writer.writerows([
                {"school_code": "B100000000001", "school_name": "高﨑小学校", "address": "東京都"},
                {"school_code": "B100000000002", "school_name": "高崎小学校", "address": "東京都"},
                {"school_code": "B100000000003", "school_name": "沢小学校", "address": "澤町"},
            ])

    def tearDown(self):
        self.temp.cleanup()

    def test_exact_precedes_variant(self):
        found = search_csv(self.path, "高崎")
        self.assertEqual([r["school_code"] for r in found], ["B100000000002", "B100000000001"])
        self.assertEqual([r["match_type"] for r in found], ["exact", "character_variant"])

    def test_unapproved_variant_not_folded(self):
        self.assertEqual([r["school_code"] for r in search_csv(self.path, "澤")], ["B100000000003"])
        self.assertEqual(search_csv(self.path, "竜"), [])

    def test_limit(self):
        self.assertEqual(len(search_csv(self.path, "高崎", limit=1)), 1)

    def test_invalid_query(self):
        with self.assertRaises(ValueError):
            search_csv(self.path, "")


if __name__ == "__main__":
    unittest.main()
