import unittest
import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from zon import ZonStreamEncoder, ZonStreamDecoder

class TestStream(unittest.IsolatedAsyncioTestCase):
    async def test_encode_stream(self):
        """Test streaming encoding."""
        async def source():
            yield {'id': 1, 'name': 'Alice'}
            yield {'id': 2, 'name': 'Bob'}

        encoder = ZonStreamEncoder()
        chunks = []
        async for chunk in encoder.encode(source()):
            chunks.append(chunk)

        result = "".join(chunks)
        self.assertIn("@:id,name", result)
        self.assertIn("1,Alice", result)
        self.assertIn("2,Bob", result)

    async def test_decode_stream(self):
        """Test streaming decoding."""
        async def source():
            yield "@:id,name\n"
            yield "1,Alice\n"
            yield "2,Bob\n"

        decoder = ZonStreamDecoder()
        items = []
        async for item in decoder.decode(source()):
            items.append(item)

        self.assertEqual(len(items), 2)
        self.assertEqual(items[0], {'id': 1, 'name': 'Alice'})
        self.assertEqual(items[1], {'id': 2, 'name': 'Bob'})

    async def test_decode_split_lines(self):
        """Test decoding stream with split lines."""
        async def source():
            yield "@:id,na"
            yield "me\n1,Al"
            yield "ice\n2,B"
            yield "ob"

        decoder = ZonStreamDecoder()
        items = []
        async for item in decoder.decode(source()):
            items.append(item)

        self.assertEqual(len(items), 2)
        self.assertEqual(items[0], {'id': 1, 'name': 'Alice'})
        self.assertEqual(items[1], {'id': 2, 'name': 'Bob'})

    async def test_round_trip(self):
        """Test streaming round-trip encoding/decoding."""
        data = [
            {'id': 1, 'val': 'A'},
            {'id': 2, 'val': 'B'},
            {'id': 3, 'val': 'C'}
        ]

        async def source():
            for item in data:
                yield item

        encoder = ZonStreamEncoder()
        decoder = ZonStreamDecoder()

        encoded_stream = encoder.encode(source())
        decoded_items = []
        async for item in decoder.decode(encoded_stream):
            decoded_items.append(item)

        self.assertEqual(decoded_items, data)

if __name__ == "__main__":
    unittest.main()
