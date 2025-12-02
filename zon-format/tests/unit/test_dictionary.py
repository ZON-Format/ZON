import unittest
from zon import ZonEncoder, ZonDecoder, decode, encode

class TestDictionaryCompression(unittest.TestCase):
    def test_detect_and_compress(self):
        """Test detection and compression of repetitive string values."""
        data = [
            {'status': 'pending' if i % 2 == 0 else 'completed',
             'priority': 'high' if i % 3 == 0 else ('medium' if i % 3 == 1 else 'low')}
            for i in range(20)
        ]

        encoder = ZonEncoder()
        encoded = encoder.encode(data)

        self.assertIn('status[', encoded)
        self.assertIn('priority[', encoded)
        self.assertRegex(encoded, r'\d,\d')

    def test_round_trip(self):
        """Test round-trip encoding/decoding with dictionary compression."""
        data = [
            {'status': 'pending', 'priority': 'high'},
            {'status': 'pending', 'priority': 'low'},
            {'status': 'completed', 'priority': 'high'},
            {'status': 'pending', 'priority': 'high'}
        ]

        encoded = encode(data)
        decoded = decode(encoded)

        self.assertEqual(decoded, data)

    def test_savings(self):
        """Test that dictionary compression actually reduces size."""
        statuses = ['pending', 'processing', 'completed', 'failed', 'cancelled']
        priorities = ['critical', 'high', 'medium', 'low', 'trivial']
        
        data = [
            {
                'id': i,
                'status': statuses[i % len(statuses)],
                'priority': priorities[i % len(priorities)],
                'category': 'general'
            }
            for i in range(100)
        ]

        encoder_with_dict = ZonEncoder(enable_dict_compression=True)
        encoded_with_dict = encoder_with_dict.encode(data)

        encoder_without_dict = ZonEncoder(enable_dict_compression=False)
        encoded_without_dict = encoder_without_dict.encode(data)

        savings = (len(encoded_without_dict) - len(encoded_with_dict)) / len(encoded_without_dict)
        self.assertGreater(savings, 0.2)

        self.assertEqual(decode(encoded_with_dict), data)
        self.assertEqual(decode(encoded_without_dict), data)

    def test_no_compress_unique(self):
        """Test that unique values are not compressed."""
        data = [
            {'id': 'uuid-1', 'name': 'Alice'},
            {'id': 'uuid-2', 'name': 'Bob'},
            {'id': 'uuid-3', 'name': 'Charlie'}
        ]

        encoded = encode(data)
        self.assertNotIn('id[', encoded)
        self.assertNotIn('name[', encoded)

    def test_mixed_columns(self):
        """Test mixture of compressed and uncompressed columns."""
        data = [
            {
                'type': 'bot' if i % 3 == 0 else 'user',
                'name': f'User{i}',
                'role': 'admin' if i % 4 == 0 else 'user'
            }
            for i in range(20)
        ]

        encoded = encode(data)
        decoded = decode(encoded)

        self.assertEqual(decoded, data)
        self.assertIn('type[', encoded)
        self.assertIn('role[', encoded)
        self.assertNotIn('name[', encoded)

if __name__ == "__main__":
    unittest.main()
