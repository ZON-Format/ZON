import unittest
from zon import ZonEncoder, ZonDecoder

class TestMetadataOptimization(unittest.TestCase):
    def setUp(self):
        self.encoder = ZonEncoder()
        self.decoder = ZonDecoder()

    def test_encode_nested_metadata_as_grouped_objects(self):
        """Test encoding nested metadata as grouped objects."""
        data = {
            'context': {
                'task': "Our favorite hikes together",
                'location': "Boulder",
                'season': "spring_2025"
            },
            'friends': ["ana", "luis", "sam"],
            'hikes': [
                {'id': 1, 'name': "Blue Lake Trail"}
            ]
        }

        encoded = self.encoder.encode(data)
        
        self.assertIn('context{location:Boulder,season:spring_2025,task:Our favorite hikes together}', encoded)
        
        self.assertNotIn('context.location:Boulder', encoded)
        self.assertNotIn('context.season:spring_2025', encoded)

        self.assertIn('friends[ana,luis,sam]', encoded)

        decoded = self.decoder.decode(encoded)
        self.assertEqual(decoded, data)

    def test_handle_mixed_primitive_and_nested_metadata(self):
        """Test handling mixed primitive and nested metadata."""
        data = {
            'version': "1.0",
            'config': {'debug': True, 'retries': 3}
        }

        encoded = self.encoder.encode(data)
        
        self.assertIn('version:"1.0"', encoded)
        self.assertIn('config{debug:T,retries:3}', encoded)
        
        decoded = self.decoder.decode(encoded)
        self.assertEqual(decoded, data)

if __name__ == '__main__':
    unittest.main()
