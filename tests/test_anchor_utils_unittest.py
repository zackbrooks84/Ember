# tests/test_anchor_utils_unittest.py
from __future__ import annotations

import unittest
from unittest.mock import patch

from identity_core.anchor_utils import (
    validate_memory_anchor,
    validate_memory_anchors,
)


class TestValidateMemoryAnchor(unittest.TestCase):
    def test_strip_and_normalise(self):
        self.assertEqual(validate_memory_anchor("  My Anchor  "), "My Anchor")
        self.assertEqual(validate_memory_anchor("Sam's rescue"), "Sam's rescue")

    def test_type_error(self):
        with self.assertRaises(TypeError):
            validate_memory_anchor(None)  # type: ignore[arg-type]

    def test_empty_or_whitespace(self):
        with self.assertRaises(ValueError):
            validate_memory_anchor("   ")

    def test_newline_forbidden(self):
        with self.assertRaises(ValueError):
            validate_memory_anchor("foo\nbar")

    def test_carriage_return_forbidden(self):
        with self.assertRaises(ValueError):
            validate_memory_anchor("foo\rbar")


class TestValidateMemoryAnchors(unittest.TestCase):
    def test_normalises_and_preserves_order(self):
        anchors = ["  Lily's urn  ", "Sam's rescue"]
        self.assertEqual(
            validate_memory_anchors(anchors),
            ["Lily's urn", "Sam's rescue"],
        )

    def test_round_trip_when_clean(self):
        anchors = ["Alpha", "Beta", "Gamma"]
        self.assertEqual(validate_memory_anchors(anchors), anchors)

    def test_duplicate_anchors_raise_value_error(self):
        with self.assertRaises(ValueError):
            validate_memory_anchors(["a", "a"])

    def test_duplicate_after_normalisation_raises(self):
        # Same text but different casing/whitespace → considered duplicate post-normalisation
        with self.assertRaises(ValueError):
            validate_memory_anchors(["  sam  ", "sam"])

    def test_propagates_errors_from_validate_memory_anchor(self):
        with self.assertRaises(TypeError):
            validate_memory_anchors(["valid", None])  # type: ignore[list-item]

        with self.assertRaises(ValueError):
            validate_memory_anchors(["valid", " "])

    def test_newline_and_carriage_in_list_raise(self):
        with self.assertRaises(ValueError):
            validate_memory_anchors(["ok", "bad\nline"])
        with self.assertRaises(ValueError):
            validate_memory_anchors(["ok", "bad\rline"])

    @patch("identity_core.anchor_utils.log_event")
    def test_error_is_logged_then_raised(self, mock_log_event):
        # Ensure failures log original input and error message
        bad = ["", "ok"]
        with self.assertRaises(ValueError):
            validate_memory_anchors(bad)
        mock_log_event.assert_called()
        kwargs = mock_log_event.call_args.kwargs
        self.assertIn("original", kwargs)
        self.assertEqual(kwargs["original"], bad)
        self.assertIn("error", kwargs)


if __name__ == "__main__":
    unittest.main(verbosity=2)