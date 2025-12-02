import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

# Mock openai module
sys.modules['openai'] = MagicMock()
sys.modules['openai.types.chat'] = MagicMock()

from zon.integrations.openai import ZOpenAI

class TestZOpenAI(unittest.TestCase):
    """Test OpenAI integration."""
    
    def setUp(self):
        self.mock_client = MagicMock()
        self.zopenai = ZOpenAI(self.mock_client)

    def test_injects_instructions_and_parses_response(self):
        """Test prompt injection and response parsing."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = 'user{name:Alice}'
        self.mock_client.chat.completions.create.return_value = mock_response

        result = self.zopenai.chat(
            messages=[{'role': 'user', 'content': 'Who is it?'}],
            model='gpt-4'
        )

        self.assertEqual(result, {'user': {'name': 'Alice'}})

        call_args = self.mock_client.chat.completions.create.call_args
        messages = call_args.kwargs['messages']
        self.assertEqual(messages[0]['role'], 'system')
        self.assertIn('RESPONSE FORMAT: You must respond in ZON', messages[0]['content'])

    def test_handles_markdown_code_blocks(self):
        """Test handling of markdown code blocks in response."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '```zon\nuser{name:Bob}\n```'
        self.mock_client.chat.completions.create.return_value = mock_response

        result = self.zopenai.chat(
            messages=[{'role': 'user', 'content': 'Who is it?'}],
            model='gpt-4'
        )

        self.assertEqual(result, {'user': {'name': 'Bob'}})

if __name__ == '__main__':
    unittest.main()
