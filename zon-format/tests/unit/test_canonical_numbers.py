"""
Canonical Number Formatting Tests

Port of canonical-numbers.test.ts from the TypeScript implementation.
Tests integer, float, and special value formatting.
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import zon


class TestCanonicalNumbers(unittest.TestCase):
    """Canonical Number Formatting tests."""

    def test_encode_integers_without_decimal_point(self):
        """Should encode integers without decimal point."""
        data = {'value': 42}
        encoded = zon.encode(data)
        
        self.assertIn('42', encoded)
        self.assertNotIn('42.0', encoded)

    def test_handle_zero(self):
        """Should handle zero."""
        data = {'value': 0}
        encoded = zon.encode(data)
        
        self.assertIn('value:0', encoded)

    def test_handle_negative_integers(self):
        """Should handle negative integers."""
        data = {'value': -123}
        encoded = zon.encode(data)
        
        self.assertIn('-123', encoded)

    def test_encode_floats_without_trailing_zeros(self):
        """Should encode floats without trailing zeros."""
        data = {'value': 3.14}
        encoded = zon.encode(data)
        
        self.assertIn('3.14', encoded)
        self.assertNotIn('3.140000', encoded)

    def test_handle_very_small_decimals(self):
        """Should handle very small decimals."""
        data = {'value': 0.001}
        encoded = zon.encode(data)
        
        self.assertIn('0.001', encoded)
        self.assertNotIn('1e-3', encoded.lower())

    def test_no_scientific_notation_for_large_numbers(self):
        """Should not use scientific notation for large numbers."""
        data = {'value': 1000000}
        encoded = zon.encode(data)
        
        self.assertIn('1000000', encoded)
        self.assertNotIn('1e6', encoded.lower())
        self.assertNotIn('1e+6', encoded.lower())

    def test_handle_numbers_with_many_decimal_places(self):
        """Should handle numbers with many decimal places."""
        data = {'value': 3.141592653589793}
        encoded = zon.encode(data)
        
        # Should preserve precision
        self.assertIn('3.14159265358979', encoded)
        # Should not contain scientific notation
        self.assertNotRegex(encoded, r'\de[+-]?\d')

    def test_encode_nan_as_null(self):
        """Should encode NaN as null."""
        data = {'value': float('nan')}
        encoded = zon.encode(data)
        
        self.assertIn('value:null', encoded)

    def test_encode_infinity_as_null(self):
        """Should encode Infinity as null."""
        data = {'value': float('inf')}
        encoded = zon.encode(data)
        
        self.assertIn('value:null', encoded)

    def test_encode_negative_infinity_as_null(self):
        """Should encode -Infinity as null."""
        data = {'value': float('-inf')}
        encoded = zon.encode(data)
        
        self.assertIn('value:null', encoded)

    def test_preserve_integer_through_roundtrip(self):
        """Should preserve integer values through round-trip."""
        data = {'value': 42}
        encoded = zon.encode(data)
        decoded = zon.decode(encoded)
        
        self.assertEqual(decoded['value'], 42)
        self.assertIsInstance(decoded['value'], int)

    def test_preserve_float_through_roundtrip(self):
        """Should preserve float values through round-trip."""
        data = {'value': 3.14}
        encoded = zon.encode(data)
        decoded = zon.decode(encoded)
        
        self.assertAlmostEqual(decoded['value'], 3.14, places=10)

    def test_preserve_large_numbers_through_roundtrip(self):
        """Should preserve large numbers through round-trip."""
        data = {'value': 1000000}
        encoded = zon.encode(data)
        decoded = zon.decode(encoded)
        
        self.assertEqual(decoded['value'], 1000000)

    def test_preserve_very_small_numbers_through_roundtrip(self):
        """Should preserve very small numbers through round-trip."""
        data = {'value': 0.000001}
        encoded = zon.encode(data)
        decoded = zon.decode(encoded)
        
        self.assertAlmostEqual(decoded['value'], 0.000001, places=10)

    def test_format_all_numbers_canonically_in_arrays(self):
        """Should format all numbers canonically in arrays."""
        data = {
            'values': [
                {'num': 1000000},
                {'num': 0.001},
                {'num': 42},
                {'num': 3.14}
            ]
        }
        
        encoded = zon.encode(data)
        
        # Should not contain scientific notation
        self.assertNotIn('e+', encoded.lower())
        self.assertNotIn('e-', encoded.lower())
        
        # Should contain actual values
        self.assertIn('1000000', encoded)
        self.assertIn('0.001', encoded)
        self.assertIn('42', encoded)
        self.assertIn('3.14', encoded)


if __name__ == '__main__':
    unittest.main()
