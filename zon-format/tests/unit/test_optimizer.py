import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from zon import LLMOptimizer, TokenCounter, encode_llm, decode

class TestLLMOptimizer(unittest.TestCase):
    def test_token_counter(self):
        """Test token counting functionality."""
        counter = TokenCounter()
        self.assertEqual(counter.count('Hello world'), 3)
        self.assertEqual(counter.count(''), 0)

    def test_optimize_field_order(self):
        """Test field order optimization for token efficiency."""
        data = [
            {'long_key_name_a': 1, 'b': 2},
            {'long_key_name_a': 1, 'b': 2}
        ]
        
        optimizer = LLMOptimizer()
        optimized = optimizer.optimize_field_order(data)
        
        self.assertIn('long_key_name_a', optimized[0])
        self.assertIn('b', optimized[0])
        self.assertEqual(len(optimized), 2)

    def test_encode_llm_retrieval(self):
        """Test LLM encoding for retrieval tasks."""
        data = [{'id': 1, 'text': "search term"}]
        context = {'task': 'retrieval', 'model': 'gpt-4'}
        
        encoded = encode_llm(data, context)
        self.assertIn('id', encoded)
        self.assertIn('search term', encoded)
        
        decoded = decode(encoded)
        self.assertEqual(decoded, data)

    def test_encode_llm_generation(self):
        """Test LLM encoding for generation tasks."""
        data = [
            {'id': 1, 'val': "A"},
            {'id': 2, 'val': "B"}
        ]
        context = {'task': 'generation', 'model': 'claude'}
        
        encoded = encode_llm(data, context)
        
        decoded = decode(encoded)
        self.assertEqual(decoded, data)

if __name__ == "__main__":
    unittest.main()
