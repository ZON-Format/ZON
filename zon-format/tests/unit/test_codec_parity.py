import unittest
import zon
from zon.core.constants import *

class TestCodecParity(unittest.TestCase):
    """
    Additional tests ported from ZON-TS/src/__tests__/codec.test.ts
    to ensure full feature parity.
    """

    def test_simple_metadata(self):
        """Test simple metadata encoding/decoding."""
        data = {'name': 'Alice', 'age': 30, 'active': True}
        encoded = zon.encode(data)
        decoded = zon.decode(encoded)
        self.assertEqual(decoded, data)

    def test_nested_object_simple(self):
        """Test simple nested object encoding/decoding."""
        data = {
            'user': {
                'name': 'Bob',
                'profile': {
                    'age': 25,
                    'city': 'NYC'
                }
            }
        }
        encoded = zon.encode(data)
        decoded = zon.decode(encoded)
        self.assertEqual(decoded, data)

    def test_array_of_objects_table(self):
        """Test array of objects (table) encoding/decoding."""
        data = [
            {'id': 1, 'name': 'Alice', 'score': 95},
            {'id': 2, 'name': 'Bob', 'score': 87},
            {'id': 3, 'name': 'Charlie', 'score': 92}
        ]
        encoded = zon.encode(data)
        decoded = zon.decode(encoded)
        self.assertEqual(decoded, data)

    def test_mixed_metadata_and_table(self):
        """Test mixed metadata and table encoding/decoding."""
        data = {
            'title': 'Sales Report',
            'year': 2024,
            'records': [
                {'month': 'Jan', 'sales': 1000},
                {'month': 'Feb', 'sales': 1200},
                {'month': 'Mar', 'sales': 1100}
            ]
        }
        encoded = zon.encode(data)
        decoded = zon.decode(encoded)
        self.assertEqual(decoded, data)

    def test_boolean_values_explicit(self):
        """Test boolean values encoding/decoding."""
        data = {
            'success': True,
            'error': False,
            'items': [
                {'id': 1, 'active': True},
                {'id': 2, 'active': False}
            ]
        }
        encoded = zon.encode(data)
        decoded = zon.decode(encoded)
        self.assertEqual(decoded, data)

    def test_null_values_mixed(self):
        """Test mixed null values encoding/decoding."""
        data = {
            'name': 'Test',
            'value': None,
            'items': [
                {'id': 1, 'data': None},
                {'id': 2, 'data': 'value'}
            ]
        }
        encoded = zon.encode(data)
        decoded = zon.decode(encoded)
        self.assertEqual(decoded, data)

    def test_numbers_mixed_types(self):
        """Test mixed number types encoding/decoding."""
        data = {
            'integer': 42,
            'float': 3.14,
            'negative': -10,
            'negativeFloat': -2.5,
            'items': [
                {'id': 1, 'value': 100},
                {'id': 2, 'value': 200.5}
            ]
        }
        encoded = zon.encode(data)
        decoded = zon.decode(encoded)
        self.assertEqual(decoded, data)

    def test_strings_special_chars(self):
        """Test strings with special characters encoding/decoding."""
        data = {
            'plain': 'hello',
            'withComma': 'hello, world',
            'withQuotes': 'say "hello"',
            'withNewline': 'line1\nline2',
            'items': [
                {'id': 1, 'text': 'normal'},
                {'id': 2, 'text': 'with, comma'}
            ]
        }
        encoded = zon.encode(data)
        decoded = zon.decode(encoded)
        self.assertEqual(decoded, data)

    def test_empty_arrays(self):
        """Test empty arrays encoding/decoding."""
        data = {
            'empty': [],
            'nested': {
                'also_empty': []
            }
        }
        encoded = zon.encode(data)
        decoded = zon.decode(encoded)
        self.assertEqual(decoded, data)

    def test_nested_arrays_in_metadata(self):
        """Test nested arrays in metadata encoding/decoding."""
        data = {
            'tags': ['javascript', 'typescript', 'node'],
            'matrix': [[1, 2], [3, 4]],
            'items': [
                {'id': 1, 'values': [10, 20]},
                {'id': 2, 'values': [30, 40]}
            ]
        }
        encoded = zon.encode(data)
        decoded = zon.decode(encoded)
        self.assertEqual(decoded, data)

    def test_complex_nested_objects_in_table(self):
        """Test complex nested objects in table encoding/decoding."""
        data = [
            {
                'id': 1,
                'metadata': {'tags': ['a', 'b'], 'count': 5}
            },
            {
                'id': 2,
                'metadata': {'tags': ['c'], 'count': 3}
            }
        ]
        encoded = zon.encode(data)
        decoded = zon.decode(encoded)
        self.assertEqual(decoded, data)

    def test_hikes_example(self):
        """Test hikes example encoding/decoding."""
        data = {
            'context': {
                'task': 'Our favorite hikes together',
                'location': 'Boulder',
                'season': 'spring_2025'
            },
            'friends': ['ana', 'luis', 'sam'],
            'hikes': [
                {
                    'id': 1,
                    'name': 'Blue Lake Trail',
                    'distanceKm': 7.5,
                    'elevationGain': 320,
                    'companion': 'ana',
                    'wasSunny': True
                },
                {
                    'id': 2,
                    'name': 'Ridge Overlook',
                    'distanceKm': 9.2,
                    'elevationGain': 540,
                    'companion': 'luis',
                    'wasSunny': False
                },
                {
                    'id': 3,
                    'name': 'Wildflower Loop',
                    'distanceKm': 5.1,
                    'elevationGain': 180,
                    'companion': 'sam',
                    'wasSunny': True
                }
            ]
        }

        encoded = zon.encode(data)
        decoded = zon.decode(encoded)
        self.assertEqual(decoded, data)

        self.assertIn('context{', encoded)
        self.assertIn('task:Our favorite hikes together', encoded)
        self.assertIn('friends[', encoded)
        self.assertIn('hikes:@(3)', encoded)

    def test_string_looks_like_number(self):
        """Test strings that look like numbers encoding/decoding."""
        data = {
            'stringNumber': '123',
            'actualNumber': 123,
            'items': [
                {'id': 1, 'code': '001'},
                {'id': 2, 'code': '002'}
            ]
        }
        encoded = zon.encode(data)
        decoded = zon.decode(encoded)
        self.assertEqual(decoded, data)
        self.assertIsInstance(decoded['stringNumber'], str)
        self.assertIsInstance(decoded['actualNumber'], int)

    def test_string_looks_like_boolean(self):
        """Test strings that look like booleans encoding/decoding."""
        data = {
            'stringTrue': 'true',
            'actualTrue': True,
            'stringFalse': 'false',
            'actualFalse': False,
            'items': [
                {'id': 1, 'status': 'T'},
                {'id': 2, 'status': True}
            ]
        }
        encoded = zon.encode(data)
        decoded = zon.decode(encoded)
        self.assertEqual(decoded, data)
        self.assertIsInstance(decoded['stringTrue'], str)
        self.assertIsInstance(decoded['actualTrue'], bool)

    def test_empty_strings(self):
        """Test empty strings encoding/decoding."""
        data = {
            'empty': '',
            'items': [
                {'id': 1, 'name': ''},
                {'id': 2, 'name': 'value'}
            ]
        }
        encoded = zon.encode(data)
        decoded = zon.decode(encoded)
        self.assertEqual(decoded, data)

    def test_whitespace_preservation(self):
        """Test whitespace preservation in strings."""
        data = {
            'leading': '  space',
            'trailing': 'space  ',
            'both': '  both  ',
            'items': [
                {'id': 1, 'text': '  padded  '}
            ]
        }
        encoded = zon.encode(data)
        decoded = zon.decode(encoded)
        self.assertEqual(decoded, data)

    def test_very_long_strings(self):
        """Test very long strings encoding/decoding."""
        long_string = 'a' * 1000
        data = {
            'long': long_string,
            'items': [
                {'id': 1, 'text': long_string}
            ]
        }
        encoded = zon.encode(data)
        decoded = zon.decode(encoded)
        self.assertEqual(decoded, data)

    def test_large_arrays(self):
        """Test large arrays encoding/decoding."""
        items = [{'id': i + 1, 'name': f'Item {i + 1}', 'value': i * 10} for i in range(100)]
        data = {'items': items}
        encoded = zon.encode(data)
        decoded = zon.decode(encoded)
        self.assertEqual(decoded, data)

    def test_array_of_primitives(self):
        """Test array of primitives encoding/decoding."""
        data = ['apple', 'banana', 'cherry']
        encoded = zon.encode(data)
        decoded = zon.decode(encoded)
        self.assertEqual(decoded, data)
        self.assertTrue(encoded.startswith('['))

    def test_deeply_nested_objects(self):
        """Test deeply nested objects encoding/decoding."""
        data = {
            'level1': {
                'level2': {
                    'level3': {
                        'level4': {
                            'value': 'deep'
                        }
                    }
                }
            }
        }
        encoded = zon.encode(data)
        decoded = zon.decode(encoded)
        self.assertEqual(decoded, data)

    def test_integer_vs_float_distinction(self):
        """Test integer vs float distinction."""
        data = {
            'integer': 42,
            'float': 42.0,
            'explicitFloat': 3.14,
            'items': [
                {'id': 1, 'intVal': 100, 'floatVal': 100.5},
                {'id': 2, 'intVal': 200, 'floatVal': 200.0}
            ]
        }
        encoded = zon.encode(data)
        decoded = zon.decode(encoded)
        
        self.assertEqual(decoded['integer'], 42)
        self.assertIsInstance(decoded['integer'], int)
        
        self.assertEqual(decoded['float'], 42.0)
        
        self.assertEqual(decoded['explicitFloat'], 3.14)
        self.assertIsInstance(decoded['explicitFloat'], float)

    def test_boolean_shorthand_tf(self):
        """Test boolean shorthand T/F."""
        data = [
            {'id': 1, 'flag': True},
            {'id': 2, 'flag': False},
            {'id': 3, 'flag': True}
        ]
        encoded = zon.encode(data)
        
        self.assertRegex(encoded, r'[,\n]T')
        self.assertRegex(encoded, r'[,\n]F')
        
        decoded = zon.decode(encoded)
        self.assertEqual(decoded, data)

if __name__ == '__main__':
    unittest.main()
