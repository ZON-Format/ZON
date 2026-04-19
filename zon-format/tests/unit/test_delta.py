import math
import unittest
from zon import ZonEncoder, ZonDecoder

class TestDeltaEncoding(unittest.TestCase):
    def setUp(self):
        self.encoder = ZonEncoder()
        self.decoder = ZonDecoder()

    def test_delta_encoding(self):
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

    def test_negative_deltas(self):
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

    def test_fallback_standard(self):
        """Test that delta encoding is not used for short sequences."""
        data = [
            {'id': 1},
            {'id': 2}
        ]
        encoded = self.encoder.encode(data)
        self.assertNotIn('id:delta', encoded)
        
        decoded = self.decoder.decode(encoded)
        self.assertEqual(decoded, data)

    def test_hierarchical_sparse(self):
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
        self.assertRegex(encoded, r'user\.details\.age:30')
        self.assertRegex(encoded, r'user\.details\.height:180')

        decoded = self.decoder.decode(encoded)
        self.assertEqual(decoded, data)

    def test_arrays_in_nested(self):
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

    def test_float_column_roundtrip_is_lossless(self):
        """Float columns must round-trip bit-exactly (spec §2.3 MUST).

        Covers multiple precision regimes so a partial fix (e.g. round-to-N)
        cannot sneak through.
        """
        data = [
            {'v': 1865.43},     # benchmark regression case
            {'v': 3579.16},     # benchmark regression case
            {'v': math.pi},     # 17-sig-digit irrational
            {'v': math.e},      # 17-sig-digit irrational
            {'v': 0.1 + 0.2},   # classic non-terminating binary: 0.30000000000000004
            {'v': -42.5},       # negative, crosses zero in deltas
            {'v': 1e-10},       # small exponent
            {'v': 1e15},        # large exponent
        ]

        decoded = self.decoder.decode(self.encoder.encode(data))

        for original, got in zip(data, decoded):
            # repr(float) is the shortest string that round-trips to the same
            # double, so repr equality is equivalent to bit equality.
            self.assertEqual(
                repr(original['v']),
                repr(got['v']),
                f"float roundtrip lost precision: {original['v']!r} -> {got['v']!r}",
            )


if __name__ == "__main__":
    unittest.main()
