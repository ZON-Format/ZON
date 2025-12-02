import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from zon import ZonEncoder, ZonDecoder

class TestAdvancedSparse(unittest.TestCase):
    def setUp(self):
        self.encoder = ZonEncoder()
        self.decoder = ZonDecoder()

    def test_delta_encoding_sequential_numbers(self):
        """Test delta encoding for sequential numeric data."""
        data = [
            {'id': 100, 'val': 10},
            {'id': 101, 'val': 20},
            {'id': 102, 'val': 15},
            {'id': 105, 'val': 30},
            {'id': 106, 'val': 31}
        ]

        encoded = self.encoder.encode(data)
        self.assertIn('id:delta', encoded)
        
        self.assertIn('100', encoded)
        self.assertIn('+1', encoded)
        self.assertIn('+3', encoded)

        decoded = self.decoder.decode(encoded)
        self.assertEqual(decoded, data)

    def test_delta_encoding_negative_deltas(self):
        """Test delta encoding with negative changes."""
        data = [
            {'temp': 20},
            {'temp': 18},
            {'temp': 15},
            {'temp': 20},
            {'temp': 10}
        ]

        encoded = self.encoder.encode(data)
        self.assertIn('temp:delta', encoded)
        self.assertIn('-2', encoded)
        self.assertIn('-3', encoded)
        self.assertIn('+5', encoded)
        self.assertIn('-10', encoded)

        decoded = self.decoder.decode(encoded)
        self.assertEqual(decoded, data)

    def test_delta_encoding_fallback_short_sequence(self):
        """Test that delta encoding is not used for short sequences."""
        data = [
            {'id': 1},
            {'id': 2}
        ]

        encoded = self.encoder.encode(data)
        self.assertNotIn('id:delta', encoded)
        
        decoded = self.decoder.decode(encoded)
        self.assertEqual(decoded, data)

    def test_hierarchical_sparse_encoding(self):
        """Test sparse encoding with nested hierarchical data."""
        data = [
            {'user': {'name': 'Alice', 'address': {'city': 'NY'}}},
            {'user': {'name': 'Bob', 'address': {'city': 'SF'}}}
        ]

        encoded = self.encoder.encode(data)
        self.assertIn('user.name', encoded)
        self.assertIn('user.address.city', encoded)
        
        self.assertNotIn('{"name":', encoded)

        decoded = self.decoder.decode(encoded)
        self.assertEqual(decoded, data)

    def test_sparse_nested_fields(self):
        """Test sparse encoding with missing nested fields."""
        data = [
            {'user': {'name': 'Alice', 'details': {'age': 30}}},
            {'user': {'name': 'Bob'}},
            {'user': {'name': 'Charlie', 'details': {'height': 180}}}
        ]

        encoded = self.encoder.encode(data)
        
        self.assertIn('user.name', encoded)
        
        self.assertIn('user.details.age:30', encoded)
        self.assertIn('user.details.height:180', encoded)

        decoded = self.decoder.decode(encoded)
        self.assertEqual(decoded, data)

    def test_arrays_within_nested_objects(self):
        """Test encoding arrays within nested objects."""
        data = [
            {'group': {'tags': ['a', 'b']}},
            {'group': {'tags': ['c']}}
        ]

        encoded = self.encoder.encode(data)
        self.assertIn('group.tags', encoded)
        self.assertIn('[a,b]', encoded)

        decoded = self.decoder.decode(encoded)
        self.assertEqual(decoded, data)
    
    def test_deep_nesting(self):
        """Test encoding of deeply nested structures."""
        data = [
            {'a': {'b': {'c': {'d': {'e': 1}}}}}
        ]
        
        encoded = self.encoder.encode(data)
        self.assertIn('a.b.c.d.e', encoded)
        
        decoded = self.decoder.decode(encoded)
        self.assertEqual(decoded, data)

if __name__ == '__main__':
    unittest.main()
