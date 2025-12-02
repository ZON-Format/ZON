import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from zon.llm.splitter import ZonSplitter
from zon import decode

class TestZonSplitter(unittest.TestCase):
    def generate_data(self, count):
        """Generate test data."""
        return [
            {
                'id': i,
                'text': f"This is item number {i} with some content to take up space.",
                'tags': ['tag1', 'tag2', 'tag3']
            }
            for i in range(count)
        ]

    def test_splits_data_into_chunks(self):
        """Test splitting data into chunks based on token limit."""
        data = self.generate_data(100)
        
        splitter = ZonSplitter(max_tokens=100)
        result = splitter.split(data)

        self.assertGreater(len(result['chunks']), 1)
        self.assertEqual(result['metadata']['total_chunks'], len(result['chunks']))
        
        for chunk in result['chunks']:
            self.assertLessEqual(len(chunk), 400)
            decoded = decode(chunk)
            self.assertTrue(isinstance(decoded, list))
            self.assertGreater(len(decoded), 0)
        
        total_items = sum(len(decode(chunk)) for chunk in result['chunks'])
        self.assertEqual(total_items, 100)

    def test_handles_overlap(self):
        """Test chunk overlap handling."""
        data = self.generate_data(10)
        splitter = ZonSplitter(max_tokens=50, overlap=1)
        result = splitter.split(data)

        decoded_chunks = [decode(c) for c in result['chunks']]
        
        for i in range(len(decoded_chunks) - 1):
            current_chunk = decoded_chunks[i]
            next_chunk = decoded_chunks[i+1]
            
            last_item = current_chunk[-1]
            first_item_next = next_chunk[0]
            
            self.assertEqual(last_item, first_item_next)

    def test_handles_single_items_larger_than_limit(self):
        """Test handling of items larger than the token limit."""
        data = [
            {'id': 1, 'text': 'Small item'},
            {'id': 2, 'text': 'A' * 1000},
            {'id': 3, 'text': 'Small item'}
        ]
        
        splitter = ZonSplitter(max_tokens=50)
        result = splitter.split(data)
        
        self.assertEqual(len(result['chunks']), 3)
        self.assertEqual(len(decode(result['chunks'][1])[0]['text']), 1000)

    def test_returns_empty_result_for_empty_input(self):
        """Test handling of empty input."""
        splitter = ZonSplitter(max_tokens=100)
        result = splitter.split([])
        
        self.assertEqual(result['chunks'], [])
        self.assertEqual(result['metadata']['total_chunks'], 0)

if __name__ == '__main__':
    unittest.main()
