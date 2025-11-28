import unittest
import zon
from zon.constants import *

class TestCodec(unittest.TestCase):
    def test_gas_encoding(self):
        """Test encoding with auto-incrementing IDs."""
        data = [{"id": i} for i in range(1, 21)]
        encoded = zon.encode(data)
        
        # v1.0.4 uses compact anonymous format @count:cols for pure lists
        self.assertIn("@20:id", encoded)
        
        decoded = zon.decode(encoded)
        self.assertEqual(len(decoded), 20)
        self.assertEqual(decoded[0]["id"], 1)
        self.assertEqual(decoded[19]["id"], 20)

    def test_liquid_encoding(self):
        """Test encoding with repeated values."""
        data = [{"status": "active"} for _ in range(5)]
        encoded = zon.encode(data)
        
        # v1.0.4 compact format
        self.assertIn("@5:status", encoded)
        
        # Decode and verify
        decoded = zon.decode(encoded)
        self.assertEqual(decoded, data)

    def test_solid_encoding(self):
        """Test encoding with random values."""
        data = [{"rand": "a"}, {"rand": "b"}, {"rand": "c"}]
        encoded = zon.encode(data)
        
        # No legacy protocol header
        self.assertNotIn("#Z:1.0", encoded)
        
        # Decode and verify
        decoded = zon.decode(encoded)
        self.assertEqual(decoded, data)

    def test_smart_packing(self):
        """Test minimal quoting for strings."""
        data = [{"name": "a1"}, {"name": "u1"}, {"name": "iv"}]
        encoded = zon.encode(data)
        
        # "a1" -> a1 (no quotes)
        self.assertIn("a1", encoded)
        self.assertNotIn('"a1"', encoded)
        
        decoded = zon.decode(encoded)
        self.assertEqual(decoded[0]["name"], "a1")

    def test_anchor(self):
        """Test roundtrip with medium-sized dataset."""
        data = [{"id": i} for i in range(1, 15)]
        encoded = zon.encode(data)

        # v1.0.4 compact format
        self.assertIn("@14:id", encoded)

        decoded = zon.decode(encoded)
        self.assertEqual(decoded, data)

    def test_null_handling(self):
        """Test null value encoding."""
        data = [{"val": None}, {"val": 1}, {"val": None}]
        encoded = zon.encode(data)
        
        # v1.0.4 uses lowercase "null"
        self.assertIn("null", encoded)
        
        # Decode and verify
        decoded = zon.decode(encoded)
        self.assertEqual(decoded, data)

    def test_rle_compression(self):
        """Test encoding with repeated column values."""
        data = [{"id": i, "status": "ok"} for i in range(1, 51)]
        encoded = zon.encode(data)

        # v1.0.4 compact format
        self.assertIn("@50:id,status", encoded)

        # Decode and verify
        decoded = zon.decode(encoded)
        self.assertEqual(decoded, data)

    def test_zmap_compression(self):
        """Test encoding with repeated string values."""
        data = [{"dept": "Engineering"}, {"dept": "MarketingDept"}, 
                {"dept": "Engineering"}, {"dept": "MarketingDept"}]
        
        encoded = zon.encode(data)

        # v1.0.4 compact format
        self.assertIn("@4:dept", encoded)

        # Decode and verify
        decoded = zon.decode(encoded)
        self.assertEqual(decoded, data)

    def test_deep_flattening(self):
        """Test nested object encoding."""
        data = [
            {"user": {"profile": {"id": 1, "theme": "dark"}}},
            {"user": {"profile": {"id": 2, "theme": "light"}}},
            {"user": {"profile": {"id": 3, "theme": "dark"}}},
            {"user": {"profile": {"id": 4, "theme": "dark"}}}
        ]
        encoded = zon.encode(data)
        
        # Ensure roundtrip works correctly
        decoded = zon.decode(encoded)
        self.assertEqual(decoded, data)

    def test_inline_mode(self):
        """Test single-row table encoding."""
        data = [{"id": 1, "name": "Alice"}]
        encoded = zon.encode(data)
        
        # No legacy protocol header
        self.assertNotIn("#Z:1.0", encoded)
        # v1.0.4 compact format
        self.assertIn("@1:id,name", encoded)
        self.assertIn("1,Alice", encoded)
        
        # Decode and verify
        decoded = zon.decode(encoded)
        self.assertEqual(decoded, data)

    def test_pattern_gas(self):
        """Test encoding with pattern strings."""
        data = [{"id": f"ORD-{i:03d}"} for i in range(1, 51)]
        encoded = zon.encode(data)

        # v1.0.4 compact format
        self.assertIn("@50:id", encoded)
        self.assertIn("ORD-001", encoded)
        
        # Decode and verify
        decoded = zon.decode(encoded)
        self.assertEqual(decoded, data)

    def test_multiplier_gas(self):
        """Test float value encoding."""
        data = [{"val": 0.52}, {"val": 0.15}, {"val": 1.00}, {"val": 0.33}]
        encoded = zon.encode(data)
        
        # Decode and verify
        decoded = zon.decode(encoded)
        self.assertEqual(decoded, data)

    def test_base62(self):
        """Test large integer encoding."""
        val = 123456789123
        data = [{"id": val}]
        encoded = zon.encode(data)
        
        # Should contain the number
        self.assertIn(str(val), encoded)
        
        # Decode and verify
        decoded = zon.decode(encoded)
        self.assertEqual(decoded, data)

if __name__ == "__main__":
    unittest.main()
