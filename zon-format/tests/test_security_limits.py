"""
Security Limits Tests (DOS Prevention)

Port of security-limits.test.ts from the TypeScript implementation.
Tests document size, line length, array length, and object key limits.
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import zon
from zon.exceptions import ZonDecodeError
from zon.constants import (
    MAX_DOCUMENT_SIZE, MAX_LINE_LENGTH, 
    MAX_ARRAY_LENGTH, MAX_OBJECT_KEYS
)


class TestSecurityLimits(unittest.TestCase):
    """Security Limits (DOS Prevention) tests."""

    def test_e301_document_size_limit_constant(self):
        """Document size limit should be 100MB."""
        self.assertEqual(MAX_DOCUMENT_SIZE, 100 * 1024 * 1024)

    def test_e301_allow_documents_under_100mb(self):
        """Should allow documents under 100MB."""
        doc = 'test:value\n' * 1000
        # Should not throw
        result = zon.decode(doc)
        self.assertIsNotNone(result)

    def test_e302_line_length_limit(self):
        """Should throw when line exceeds 1MB (E302)."""
        long_line = 'key:' + 'x' * (MAX_LINE_LENGTH + 1)
        
        with self.assertRaises(ZonDecodeError) as context:
            zon.decode(long_line)
        
        self.assertIn('E302', str(context.exception))

    def test_e302_allow_lines_under_1mb(self):
        """Should allow lines under 1MB."""
        line = 'key:' + 'x' * 1000
        result = zon.decode(line)
        self.assertIn('key', result)

    def test_e303_array_length_limit_constant(self):
        """Array length limit should be 1 million items."""
        self.assertEqual(MAX_ARRAY_LENGTH, 1_000_000)

    def test_e304_object_key_limit_constant(self):
        """Object key limit should be 100K keys."""
        self.assertEqual(MAX_OBJECT_KEYS, 100_000)

    def test_e304_allow_objects_under_100k_keys(self):
        """Should allow objects under 100K keys."""
        keys = ','.join([f'k{i}:{i}' for i in range(100)])
        zon_data = f'data:"{{{{ {keys} }}}}"'
        
        result = zon.decode(f'data:"{{{keys}}}"')
        self.assertIn('data', result)

    def test_nesting_depth_limit_throw(self):
        """Should throw when nesting exceeds 100 levels."""
        nested = '[' * 150 + ']' * 150
        
        with self.assertRaises(ZonDecodeError) as context:
            zon.decode(nested)
        
        self.assertIn('Maximum nesting depth exceeded', str(context.exception))

    def test_nesting_depth_limit_allow_under_100(self):
        """Should allow nesting under 100 levels."""
        nested = '[' * 50 + ']' * 50
        result = zon.decode(nested)
        self.assertIsNotNone(result)

    def test_combined_limits_normal_data(self):
        """Should work with normal data within all limits."""
        zon_data = '''
metadata:"{version:1.0.4,env:prod}"
users:@(3):id,name
1,Alice
2,Bob
3,Carol
tags:"[nodejs,typescript,llm]"
'''
        result = zon.decode(zon_data)
        self.assertEqual(len(result['users']), 3)
        self.assertEqual(result['metadata']['version'], '1.0.4')
        self.assertEqual(len(result['tags']), 3)


if __name__ == '__main__':
    unittest.main()
