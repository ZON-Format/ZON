"""
Encoder Conformance Tests

Port of conformance-encoder.test.ts from the TypeScript implementation.
Tests based on FORMAL_SPEC.md §11.1 Encoder Checklist.
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import zon


class TestEncoderConformance(unittest.TestCase):
    """Encoder Conformance tests (§11.1)."""

    def test_emit_utf8_with_lf_line_endings(self):
        """Should emit UTF-8 with LF line endings."""
        data = {'a': 1, 'b': 2}
        encoded = zon.encode(data)
        
        # Should use LF, not CRLF
        self.assertNotIn('\r\n', encoded)
        # Should be a string
        self.assertIsInstance(encoded, str)

    def test_encode_booleans_as_tf(self):
        """Should encode booleans as T/F."""
        data = {'active': True, 'archived': False}
        encoded = zon.encode(data)
        
        self.assertIn('active:T', encoded)
        self.assertIn('archived:F', encoded)
        self.assertNotIn('true', encoded.lower())
        self.assertNotIn('false', encoded.lower())

    def test_encode_null_as_null(self):
        """Should encode null as "null"."""
        data = {'value': None}
        encoded = zon.encode(data)
        
        self.assertIn('value:null', encoded)

    def test_emit_canonical_numbers(self):
        """Should emit canonical numbers."""
        data = {'int': 42, 'float': 3.14, 'big': 1000000}
        encoded = zon.encode(data)
        
        # No scientific notation
        self.assertIn('1000000', encoded)
        self.assertNotIn('1e6', encoded.lower())
        self.assertNotIn('1e+6', encoded.lower())
        
        # Has decimal for floats
        self.assertIn('3.14', encoded)

    def test_normalize_nan_infinity_to_null(self):
        """Should normalize NaN/Infinity to null."""
        data = {'nan': float('nan'), 'inf': float('inf'), 'neg_inf': float('-inf')}
        encoded = zon.encode(data)
        
        self.assertIn('nan:null', encoded)
        self.assertIn('inf:null', encoded)
        self.assertIn('neg_inf:null', encoded)

    def test_detect_uniform_arrays_table_format(self):
        """Should detect uniform arrays → table format."""
        data = {
            'users': [
                {'id': 1, 'name': 'Alice'},
                {'id': 2, 'name': 'Bob'}
            ]
        }
        encoded = zon.encode(data)
        
        # Should have table marker
        self.assertRegex(encoded, r'users:@\(\d+\)')
        self.assertIn('id,name', encoded)

    def test_emit_table_headers_with_count_and_columns(self):
        """Should emit table headers with count and columns."""
        data = {
            'items': [
                {'x': 1, 'y': 2},
                {'x': 3, 'y': 4},
                {'x': 5, 'y': 6}
            ]
        }
        encoded = zon.encode(data)
        
        self.assertIn('items:@(3):', encoded)

    def test_sort_columns_alphabetically(self):
        """Should sort columns alphabetically."""
        data = {
            'records': [
                {'z': 1, 'a': 2, 'm': 3}
            ]
        }
        encoded = zon.encode(data)
        
        # Columns should be sorted: a, m, z
        self.assertRegex(encoded, r'records:@\(1\):a,m,z')

    def test_quote_strings_with_special_characters(self):
        """Should quote strings with special characters."""
        data = {
            'comma': 'a,b',
            'colon': 'x:y',
            'quote': 'say "hi"'
        }
        encoded = zon.encode(data)
        
        self.assertIn('"a,b"', encoded)
        self.assertIn('"x:y"', encoded)
        # Uses quote doubling: " becomes ""
        self.assertIn('""hi""', encoded)

    def test_escape_quotes_in_strings(self):
        """Should escape quotes in strings."""
        data = {'text': 'he said "hello"'}
        encoded = zon.encode(data)
        
        # Uses quote doubling
        self.assertIn('""hello""', encoded)

    def test_produce_deterministic_output(self):
        """Should produce deterministic output."""
        data = {'b': 2, 'a': 1, 'c': 3}
        
        encoded1 = zon.encode(data)
        encoded2 = zon.encode(data)
        
        self.assertEqual(encoded1, encoded2)

    def test_handle_empty_objects(self):
        """Should handle empty objects."""
        data = {}
        encoded = zon.encode(data)
        
        self.assertEqual(encoded, '{}')

    def test_handle_empty_arrays(self):
        """Should handle empty arrays."""
        data = {'items': []}
        encoded = zon.encode(data)
        
        self.assertTrue(len(encoded) > 0)


if __name__ == '__main__':
    unittest.main()
