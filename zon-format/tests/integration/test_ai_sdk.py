import unittest
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from zon.integrations.ai_sdk import parse_zon_stream

class TestAiSdk(unittest.IsolatedAsyncioTestCase):
    """Test AI SDK integration."""
    
    async def test_parse_zon_stream(self):
        """Test parsing a ZON stream."""
        async def source():
            yield "@:id,name\n"
            yield "1,Alice\n"
            yield "2,Bob\n"

        items = []
        async for item in parse_zon_stream(source()):
            items.append(item)

        self.assertEqual(len(items), 2)
        self.assertEqual(items[0], {'id': 1, 'name': 'Alice'})
        self.assertEqual(items[1], {'id': 2, 'name': 'Bob'})

if __name__ == '__main__':
    unittest.main()
