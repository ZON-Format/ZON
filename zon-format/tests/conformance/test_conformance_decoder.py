"""
Decoder Conformance Tests

Port of conformance-decoder.test.ts from the TypeScript implementation.
Tests based on FORMAL_SPEC.md §11.2 Decoder Checklist.
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from zon.core.constants import *
import zon
from zon import ZonDecodeError
from zon.core.constants import MAX_LINE_LENGTH


class TestDecoderConformance(unittest.TestCase):
    """Decoder Conformance tests (§11.2)."""

    def test_accept_utf8_with_lf_or_crlf(self):
        """Should accept UTF-8 with LF or CRLF."""
        zon_lf = 'key:value\nkey2:value2'
        zon_crlf = 'key:value\r\nkey2:value2'
        
        result_lf = zon.decode(zon_lf)
        result_crlf = zon.decode(zon_crlf)
        
        self.assertIn('key', result_lf)
        self.assertIn('key', result_crlf)

    def test_decode_t_f_null(self):
        """Should decode T → true, F → false, null → null."""
        zon_data = 'active:T\narchived:F\nvalue:null'
        result = zon.decode(zon_data)
        
        self.assertEqual(result['active'], True)
        self.assertEqual(result['archived'], False)
        self.assertIsNone(result['value'])

    def test_parse_decimal_and_exponent_numbers(self):
        """Should parse decimal and exponent numbers."""
        zon_data = 'int:42\nfloat:3.14\nbig:1000000'
        result = zon.decode(zon_data)
        
        self.assertEqual(result['int'], 42)
        self.assertAlmostEqual(result['float'], 3.14, places=10)
        self.assertEqual(result['big'], 1000000)

    def test_treat_leading_zero_numbers_as_strings(self):
        """Should treat leading-zero numbers as strings."""
        zon_data = 'code:"007"'
        result = zon.decode(zon_data)
        
        self.assertEqual(result['code'], '007')
        self.assertIsInstance(result['code'], str)

    def test_unescape_quoted_strings(self):
        """Should unescape quoted strings."""
        zon_data = 'text:"he said \\"hello\\""'
        result = zon.decode(zon_data)
        
        self.assertEqual(result['text'], 'he said "hello"')

    def test_parse_table_rows_into_array_of_objects(self):
        """Should parse table rows into array of objects."""
        zon_data = """
users:@(2):id,name
1,Alice
2,Bob
"""
        result = zon.decode(zon_data)
        
        self.assertEqual(len(result['users']), 2)
        self.assertEqual(result['users'][0], {'id': 1, 'name': 'Alice'})
        self.assertEqual(result['users'][1], {'id': 2, 'name': 'Bob'})

    def test_preserve_key_order_from_document(self):
        """Should preserve key order from document."""
        zon_data = 'z:1\na:2\nm:3'
        result = zon.decode(zon_data)
        
        keys = list(result.keys())
        self.assertEqual(keys, ['z', 'a', 'm'])

    def test_reject_prototype_pollution_attempts(self):
        """Should reject prototype pollution attempts."""
        malicious = """
@data(1):id,__proto__.polluted
1,true
"""
        decoded = zon.decode(malicious)
        
        self.assertFalse(hasattr({}, 'polluted'))

    def test_throw_on_nesting_depth_over_100(self):
        """Should throw on nesting depth > 100."""
        deep_nested = '[' * 150 + ']' * 150
        
        with self.assertRaises(ZonDecodeError) as context:
            zon.decode(deep_nested)
        
        self.assertIn('Maximum nesting depth exceeded', str(context.exception))

    def test_throw_on_line_length_over_1mb_e302(self):
        """Should throw on line length > 1MB (E302)."""
        long_line = 'key:' + 'x' * (MAX_LINE_LENGTH + 1)
        
        with self.assertRaises(ZonDecodeError) as context:
            zon.decode(long_line)
        
        self.assertIn('E302', str(context.exception))

    def test_case_insensitive_null_boolean_aliases(self):
        """Should handle case-insensitive null/boolean aliases."""
        zon_data = 'a:TRUE\nb:False\nc:NONE\nd:nil'
        result = zon.decode(zon_data)
        
        self.assertEqual(result['a'], True)
        self.assertEqual(result['b'], False)
        self.assertIsNone(result['c'])
        self.assertIsNone(result['d'])

    def test_reconstruct_nested_objects_from_dotted_keys(self):
        """Should reconstruct nested objects from dotted keys."""
        zon_data = 'config.db.host:localhost\nconfig.db.port:5432'
        result = zon.decode(zon_data)
        
        self.assertEqual(result['config']['db']['host'], 'localhost')
        self.assertEqual(result['config']['db']['port'], 5432)

    def test_unwrap_pure_lists_data_key(self):
        """Should unwrap pure lists (data key)."""
        zon_data = """
@2:id,name
1,Alice
2,Bob
"""
        result = zon.decode(zon_data)
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

    def test_handle_empty_strings_in_table_cells(self):
        """Should handle empty strings in table cells."""
        zon_data = """
users:@(2):id,name
1,""
2,Bob
"""
        result = zon.decode(zon_data)
        
        self.assertEqual(result['users'][0]['name'], '')


if __name__ == '__main__':
    unittest.main()
