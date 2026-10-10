"""Regression tests for conservative Unicode search equivalence."""
import unittest
from scripts.search_normalization import matches_search, normalize_search


class SearchNormalizationTests(unittest.TestCase):
    def test_equivalent_variants(self):
        for original, ordinary in (("塚", "塚"), ("﨑", "崎"), ("都", "都")):
            with self.subTest(original=original):
                self.assertEqual(normalize_search(original), ordinary)
                self.assertTrue(matches_search(ordinary, "高" + original + "学校"))
                self.assertTrue(matches_search(original, "高" + ordinary + "学校"))

    def test_preserve_unrelated_compatibility_characters(self):
        self.assertEqual(normalize_search("ℐ ⁺ − ⼤"), "ℐ ⁺ − ⼤")

    def test_preserve_variation_selectors_and_pua(self):
        text = "葛\U000E0100\uEF54"
        self.assertEqual(normalize_search(text), text)

    def test_input_unchanged(self):
        source = "高﨑学校"
        normalize_search(source)
        self.assertEqual(source, "高﨑学校")

    def test_type_error(self):
        with self.assertRaises(TypeError):
            normalize_search(None)


if __name__ == "__main__":
    unittest.main()
