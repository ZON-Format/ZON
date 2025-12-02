import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from zon import ZonEncoder, ZonDecoder

class TestTypeCoercion(unittest.TestCase):
    def setUp(self):
        self.decoder = ZonDecoder()

    def test_coerce_numeric_strings_to_numbers(self):
        """Test coercing numeric strings to numbers."""
        data = [
            {'id': '1', 'score': '95'},
            {'id': '2', 'score': '87'}
        ]

        encoder = ZonEncoder(enable_type_coercion=True)
        encoded = encoder.encode(data)
        
        self.assertIn('1,95', encoded)
        self.assertNotIn('"1"', encoded)
        self.assertNotIn('"95"', encoded)

        decoded = self.decoder.decode(encoded, type_coercion=True)
        self.assertIsInstance(decoded[0]['id'], int)
        self.assertIsInstance(decoded[0]['score'], int)
        self.assertEqual(decoded[0]['id'], 1)

    def test_not_coerce_when_disabled(self):
        """Test that coercion does not happen when disabled."""
        data = [
            {'id': '1', 'score': '95'}
        ]

        encoder = ZonEncoder()
        encoded = encoder.encode(data)
        
        self.assertIn('"1"', encoded)
        
        decoded = self.decoder.decode(encoded)
        self.assertIsInstance(decoded[0]['id'], str)
        self.assertEqual(decoded[0]['id'], '1')

    def test_coerce_boolean_strings(self):
        """Test coercing boolean strings."""
        data = [
            {'active': 'true'},
            {'active': 'FALSE'},
            {'active': '1'},
            {'active': '0'}
        ]

        encoder = ZonEncoder(enable_type_coercion=True)
        encoded = encoder.encode(data)
        
        self.assertIn('T', encoded)
        self.assertIn('F', encoded)
        
        decoded = self.decoder.decode(encoded, type_coercion=True)
        self.assertIs(decoded[0]['active'], True)
        self.assertIs(decoded[1]['active'], False)
        self.assertIs(decoded[2]['active'], True)
        self.assertIs(decoded[3]['active'], False)

    def test_coerce_json_strings(self):
        """Test coercing JSON strings."""
        data = [
            {'config': '{"a":1}'},
            {'config': '{"b":2}'}
        ]

        encoder = ZonEncoder(enable_type_coercion=True)
        encoded = encoder.encode(data)
        
        self.assertIn('{a:1}', encoded)
        self.assertNotIn('"{\\"a\\":1}"', encoded)

        decoded = self.decoder.decode(encoded, type_coercion=True)
        self.assertIsInstance(decoded[0]['config'], dict)
        self.assertEqual(decoded[0]['config']['a'], 1)

    def test_not_coerce_mixed_types(self):
        """Test that mixed types are not coerced."""
        data = [
            {'val': '123'},
            {'val': 'abc'}
        ]

        encoder = ZonEncoder(enable_type_coercion=True)
        encoded = encoder.encode(data)
        
        self.assertIn('"123"', encoded)
        self.assertIn('abc', encoded)

        decoded = self.decoder.decode(encoded, type_coercion=True)
        self.assertIsInstance(decoded[0]['val'], str)

if __name__ == '__main__':
    unittest.main()
