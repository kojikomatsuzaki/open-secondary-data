"""Regression tests for search-only Unicode equivalence policy."""
import tempfile
import unittest
from pathlib import Path

from scripts.search_normalization import load_search_aliases, matches_search, normalize_search


class SearchNormalizationTests(unittest.TestCase):
    def test_approved_variants_both_directions(self):
        for original, ordinary in (("塚", "塚"), ("﨑", "崎"), ("都", "都")):
            with self.subTest(original=original):
                self.assertEqual(normalize_search(original), ordinary)
                self.assertTrue(matches_search(ordinary, "高" + original + "学校"))
                self.assertTrue(matches_search(original, "高" + ordinary + "学校"))

    def test_candidate_mappings_are_not_active(self):
        for text in ("沢澤", "龍竜", "旧舊", "体體", "崎嵜", "ケヶガカがか箇个"):
            self.assertEqual(normalize_search(text), text)

    def test_preserve_unrelated_symbols(self):
        self.assertEqual(normalize_search("ℐ ⁺ − ⼤"), "ℐ ⁺ − ⼤")

    def test_preserve_ivs_and_pua(self):
        text = "葛\U000E0100\uEF54"
        self.assertEqual(normalize_search(text), text)

    def test_input_unchanged(self):
        source = "高﨑学校"
        normalize_search(source)
        self.assertEqual(source, "高﨑学校")

    def test_reject_invalid_mapping(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.yaml"
            path.write_text("automatic:\n  - canonical: '崎'\n    variants: ['嵜']\n    scope: 'source_rewrite'\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_search_aliases(path)

    def test_type_error(self):
        with self.assertRaises(TypeError):
            normalize_search(None)


if __name__ == "__main__":
    unittest.main()
