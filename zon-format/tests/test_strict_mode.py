"""
Strict Mode Validation Tests

Port of strict-mode.test.ts from the TypeScript implementation.
Tests row count mismatch (E001) and field count mismatch (E002) errors.
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import zon
from zon.exceptions import ZonDecodeError


class TestStrictMode(unittest.TestCase):
    """Strict Mode Validation tests."""

    def test_e001_row_count_mismatch_strict_mode(self):
        """Should throw when table has fewer rows than declared (strict mode)."""
        zon_data = """
users:@(3):id,name
1,Alice
2,Bob
"""
        with self.assertRaises(ZonDecodeError) as context:
            zon.decode(zon_data)
        
        self.assertIn('Row count mismatch', str(context.exception))
        self.assertEqual(context.exception.code, 'E001')

    def test_e001_row_count_mismatch_non_strict(self):
        """Should allow row count mismatch in non-strict mode."""
        zon_data = """
users:@(3):id,name
1,Alice
2,Bob
"""
        result = zon.decode(zon_data, strict=False)
        # Non-strict mode allows fewer rows
        self.assertEqual(len(result['users']), 2)

    def test_e001_row_count_matches_strict(self):
        """Should pass when row count matches (strict mode)."""
        zon_data = """
users:@(2):id,name
1,Alice
2,Bob
"""
        result = zon.decode(zon_data)
        self.assertEqual(len(result['users']), 2)
        self.assertEqual(result['users'][0], {'id': 1, 'name': 'Alice'})

    def test_e002_field_count_mismatch_strict(self):
        """Should throw when row has fewer fields than declared columns (strict mode)."""
        zon_data = """
users:@(2):id,name,role
1,Alice
2,Bob,admin
"""
        with self.assertRaises(ZonDecodeError) as context:
            zon.decode(zon_data)
        
        self.assertIn('Field count mismatch', str(context.exception))
        self.assertEqual(context.exception.code, 'E002')

    def test_e002_field_count_mismatch_non_strict(self):
        """Should allow missing fields in non-strict mode."""
        zon_data = """
users:@(2):id,name,role
1,Alice
2,Bob,admin
"""
        result = zon.decode(zon_data, strict=False)
        self.assertEqual(len(result['users']), 2)
        self.assertEqual(result['users'][0]['id'], 1)
        self.assertEqual(result['users'][0]['name'], 'Alice')
        self.assertEqual(result['users'][1], {'id': 2, 'name': 'Bob', 'role': 'admin'})

    def test_e002_field_count_matches_strict(self):
        """Should pass when all rows have correct field count (strict mode)."""
        zon_data = """
users:@(2):id,name,role
1,Alice,user
2,Bob,admin
"""
        result = zon.decode(zon_data)
        self.assertEqual(len(result['users']), 2)
        self.assertEqual(result['users'][0], {'id': 1, 'name': 'Alice', 'role': 'user'})

    def test_sparse_fields_allowed_strict(self):
        """Should allow sparse fields even in strict mode."""
        zon_data = """
users:@(2):id,name
1,Alice,role:admin,score:98
2,Bob
"""
        result = zon.decode(zon_data)
        self.assertEqual(result['users'][0], {'id': 1, 'name': 'Alice', 'role': 'admin', 'score': 98})
        self.assertEqual(result['users'][1], {'id': 2, 'name': 'Bob'})

    def test_error_includes_code(self):
        """Should include error code in error object."""
        zon_data = """users:@(2):id,name
1,Alice"""
        
        with self.assertRaises(ZonDecodeError) as context:
            zon.decode(zon_data)
        
        self.assertEqual(context.exception.code, 'E001')

    def test_error_includes_context(self):
        """Should include context in error message."""
        zon_data = """users:@(2):id,name
1,Alice"""
        
        with self.assertRaises(ZonDecodeError) as context:
            zon.decode(zon_data)
        
        self.assertIsNotNone(context.exception.context)
        self.assertIn('Table: users', str(context.exception))

    def test_strict_mode_enabled_by_default(self):
        """Strict mode should be enabled by default."""
        zon_data = """
users:@(2):id,name
1,Alice
"""
        # Should throw because default is strict=True
        with self.assertRaises(ZonDecodeError):
            zon.decode(zon_data)

    def test_can_explicitly_enable_strict(self):
        """Can explicitly enable strict mode."""
        zon_data = """
users:@(2):id,name
1,Alice
"""
        with self.assertRaises(ZonDecodeError):
            zon.decode(zon_data, strict=True)

    def test_validate_multiple_tables_independently(self):
        """Should validate multiple tables independently."""
        zon_data = """
users:@(2):id,name
1,Alice
2,Bob
products:@(1):id,title
100,Widget
"""
        result = zon.decode(zon_data)
        self.assertEqual(len(result['users']), 2)
        self.assertEqual(len(result['products']), 1)

    def test_valid_data_multiple_tables(self):
        """Should work with valid data across multiple tables."""
        zon_data = """
users:@(2):id,name
1,Alice
2,Bob
products:@(2):id,title
100,Widget
200,Gadget
"""
        result = zon.decode(zon_data)
        self.assertEqual(len(result['users']), 2)
        self.assertEqual(len(result['products']), 2)


if __name__ == '__main__':
    unittest.main()
