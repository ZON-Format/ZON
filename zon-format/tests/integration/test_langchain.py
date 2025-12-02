import unittest
from unittest.mock import MagicMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

# Mock langchain_core module
mock_langchain = MagicMock()
class MockBaseOutputParser:
    pass
mock_langchain.output_parsers.BaseOutputParser = MockBaseOutputParser
sys.modules['langchain_core'] = mock_langchain
sys.modules['langchain_core.output_parsers'] = mock_langchain.output_parsers

from zon.integrations.langchain import ZonOutputParser

class TestZonOutputParser(unittest.TestCase):
    """Test LangChain integration."""
    
    def setUp(self):
        self.parser = ZonOutputParser()

    def test_get_format_instructions(self):
        """Test format instructions generation."""
        instructions = self.parser.get_format_instructions()
        self.assertIn('Your response must be formatted as ZON', instructions)
        self.assertIn("Use 'key:value' for properties", instructions)

    def test_parses_clean_zon(self):
        """Test parsing clean ZON output."""
        text = "user{name:Alice,role:admin}"
        result = self.parser.parse(text)
        self.assertEqual(result, {'user': {'name': 'Alice', 'role': 'admin'}})

    def test_parses_markdown_zon(self):
        """Test parsing ZON inside markdown block."""
        text = "```zon\nuser{name:Bob}\n```"
        result = self.parser.parse(text)
        self.assertEqual(result, {'user': {'name': 'Bob'}})

    def test_parses_markdown_zonf(self):
        """Test parsing ZON inside markdown block with zonf extension."""
        text = "```zonf\nuser{name:Charlie}\n```"
        result = self.parser.parse(text)
        self.assertEqual(result, {'user': {'name': 'Charlie'}})

    def test_raises_error_on_invalid_zon(self):
        """Test error handling for invalid ZON."""
        text = "users:@(abc):id,name"
        with self.assertRaises(ValueError) as context:
            self.parser.parse(text)
        self.assertIn('Failed to parse ZON output', str(context.exception))

if __name__ == '__main__':
    unittest.main()
