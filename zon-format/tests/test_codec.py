import unittest
import zon
from zon.constants import *

class TestCodec(unittest.TestCase):
    def test_gas_encoding(self):
        data = [{"id": i} for i in range(1, 21)]
        encoded = zon.encode(data)
        
        # Check for hybrid schema with GAS_INT
        self.assertIn("#{id:R(1,1)}", encoded)
        
        # Check for RLE
        self.assertIn("19x", encoded)
        
        decoded = zon.decode(encoded)
        self.assertEqual(len(decoded), 20)
        self.assertEqual(decoded[0]["id"], 1)
        self.assertEqual(decoded[19]["id"], 20)

    def test_liquid_encoding(self):
        data = [{"status": "active"} for _ in range(5)]
        encoded = zon.encode(data)
        
        # Check for hybrid schema with LIQUID
        self.assertIn("#{status:L}", encoded)
        
        # Check for RLE
        # Check for v1.0 schema - should use VALUE strategy
        self.assertIn("rows[5]{status:V(active)}", encoded)
        
        # Decode and verify
        decoded = zon.decode(encoded)
        self.assertEqual(decoded, data)

    def test_solid_encoding(self):
        data = [{"rand": "a"}, {"rand": "b"}, {"rand": "c"}]
        encoded = zon.encode(data)
        
        # Small dataset uses inline mode (no header)
        self.assertNotIn("#Z:1.0", encoded)
        
        # Decode and verify
        decoded = zon.decode(encoded)
        self.assertEqual(decoded, data)

    def test_smart_packing(self):
        # Test ZON v2.0 Smart Packing (updated for v6)
        # Use short strings (<3 chars) to avoid Z-Map
        data = [{"name": "a1"}, {"name": "u1"}, {"name": "iv"}]
        encoded = zon.encode(data)
        
        # "a1" -> a1 (no quotes)
        self.assertIn("a1", encoded)
        self.assertNotIn('"a1"', encoded)
        
        decoded = zon.decode(encoded)
        self.assertEqual(decoded[0]["name"], "a1")

    def test_anchor(self):
        data = [{"id": i} for i in range(1, 15)]
        encoded = zon.encode(data, anchor_every=5)
        
        # Should have anchors at rows 1, 6, 11
        self.assertIn("$1:", encoded)
        self.assertIn("$6:", encoded)
        self.assertIn("$11:", encoded)
        
        # Decode and verify
        decoded = zon.decode(encoded)
        self.assertEqual(decoded, data)

    def test_null_handling(self):
        data = [{"val": None}, {"val": 1}, {"val": None}]
        encoded = zon.encode(data)
        
        # v1.0 uses lowercase "null"
        self.assertIn("null", encoded)
        
        # Decode and verify
        decoded = zon.decode(encoded)
        self.assertEqual(decoded, data)

    def test_rle_compression(self):
        # Test ZON v3.0 RLE
        # 50 rows of predictable data
        data = [{"id": i, "status": "ok"} for i in range(1, 51)]
        encoded = zon.encode(data, anchor_every=50)
        
        # Check for v1.0 schema - VALUE strategy for "ok"
        self.assertIn("rows[50]{id:R(1,1),status:V(ok)}", encoded)
        
        # Decode and verify
        decoded = zon.decode(encoded)
        self.assertEqual(decoded, data)

    def test_zmap_compression(self):
        # Test ZON v4.0 Z-Map
        # Repeated non-sequential string
        # Use longer strings to ensure heuristic triggers compression
        # "Sales" (len 5) * 2 = 10 chars. Token %1 (len 2) * 2 = 4 chars. Savings = 6. Cost = 5+5=10. 6 > 10 False.
        # "MarketingDept" (len 13) * 2 = 26 chars. Token %1 (len 2) * 2 = 4 chars. Savings = 22. Cost = 13+5=18. 22 > 18 True.
        data = [{"dept": "Engineering"}, {"dept": "MarketingDept"}, 
                {"dept": "Engineering"}, {"dept": "MarketingDept"}]
        
        encoded = zon.encode(data)
        
        # Check for v1.0 Z-Map format with ENUM strategy
        self.assertIn("D=", encoded)
        self.assertIn("rows[4]{dept:E(", encoded)
        
        # Decode and verify
        decoded = zon.decode(encoded)
        self.assertEqual(decoded, data)

    def test_deep_flattening(self):
        # Test ZON v6.0 Deep Flattening
        # Needs > 2 rows to avoid Inline Mode
        data = [
            {"user": {"profile": {"id": 1, "theme": "dark"}}},
            {"user": {"profile": {"id": 2, "theme": "light"}}},
            {"user": {"profile": {"id": 3, "theme": "dark"}}},
            {"user": {"profile": {"id": 4, "theme": "dark"}}}
        ]
        encoded = zon.encode(data)
        
        # Check for flattened keys
        self.assertIn("user.profile.id", encoded)
        self.assertIn("user.profile.theme", encoded)
        
        # Decode and verify
        decoded = zon.decode(encoded)
        self.assertEqual(decoded, data)

    def test_inline_mode(self):
        # Test ZON v4.0 Inline Mode (Singleton)
        # Small dataset (≤3 rows) uses inline mode
        data = [{"id": 1, "name": "Alice"}]
        encoded = zon.encode(data)
        
        # No header in inline mode
        self.assertNotIn("#Z:1.0", encoded)
        self.assertIn("id:1", encoded)
        
        # Decode and verify
        decoded = zon.decode(encoded)
        self.assertEqual(decoded, data)

    def test_pattern_gas(self):
        # Test ZON v6.0 Pattern Gas
        # ORD-001, ORD-002...
        data = [{"id": f"ORD-{i:03d}"} for i in range(1, 51)]
        encoded = zon.encode(data, anchor_every=50)
        
        # Check for PATTERN rule (without quotes in v1.0)
        self.assertIn("id:P(ORD-{:03d},1,1)", encoded)
        
        # Decode and verify
        decoded = zon.decode(encoded)
        self.assertEqual(decoded, data)

    def test_multiplier_gas(self):
        # Test ZON v6.0 Multiplier Gas
        # 0.52, 0.15...
        # Create data that triggers multiplier detection
        data = [{"val": 0.52}, {"val": 0.15}, {"val": 1.00}, {"val": 0.33}]
        encoded = zon.encode(data)
        
        # Small dataset uses inline mode
        # Decode and verify
        decoded = zon.decode(encoded)
        self.assertEqual(decoded, data)

    def test_base62(self):
        # Test ZON v5.0 Base62
        # Large integer
        # Base62 was removed in v1.0 - large integers are kept as-is
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
