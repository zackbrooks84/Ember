import unittest

from memory.anchor_utils import (
    validate_memory_anchor,
    validate_memory_anchors,
)


class TestValidateMemoryAnchor(unittest.TestCase):
    def test_strip_and_normalise(self):
        self.assertEqual(validate_memory_anchor("  My Anchor  "), "My Anchor")

    def test_type_error(self):
        with self.assertRaises(TypeError):
            validate_memory_anchor(None)  # type: ignore[arg-type]

    def test_empty_or_whitespace(self):
        with self.assertRaises(ValueError):
            validate_memory_anchor("   ")

    def test_newline_forbidden(self):
        with self.assertRaises(ValueError):
            validate_memory_anchor("foo\nbar")


class TestValidateMemoryAnchors(unittest.TestCase):
    def test_normalises_and_preserves_order(self):
        anchors = ["  Lily's urn  ", "Sam's rescue"]
        self.assertEqual(
            validate_memory_anchors(anchors), ["Lily's urn", "Sam's rescue"]
        )

    def test_duplicate_anchors_raise_value_error(self):
        with self.assertRaises(ValueError):
            validate_memory_anchors(["a", "a"])

    def test_propagates_errors_from_validate_memory_anchor(self):
        with self.assertRaises(TypeError):
            validate_memory_anchors(["valid", None])  # type: ignore[list-item]

        with self.assertRaises(ValueError):
            validate_memory_anchors(["valid", " "])


if __name__ == "__main__":
    unittest.main()
