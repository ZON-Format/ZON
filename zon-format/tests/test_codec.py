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
        self.assertIn("4x", encoded)
        
        decoded = zon.decode(encoded)
        self.assertEqual(len(decoded), 5)
        self.assertTrue(all(d["status"] == "active" for d in decoded))

    def test_solid_encoding(self):
        data = [{"rand": "a"}, {"rand": "b"}, {"rand": "c"}]
        encoded = zon.encode(data)
        
        # Check for hybrid schema with SOLID
        self.assertIn("#{rand:S}", encoded)
        
        decoded = zon.decode(encoded)
        self.assertEqual(decoded[0]["rand"], "a")
        self.assertEqual(decoded[1]["rand"], "b")
        self.assertEqual(decoded[2]["rand"], "c")

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
        # Use explicit anchor_every for testing
        encoded = zon.encode(data, anchor_every=3)
        
        # Should have anchors at rows 1, 4, 7, 10, 13
        self.assertIn("$1:", encoded)
        self.assertIn("$4:", encoded)
        
        decoded = zon.decode(encoded)
        self.assertEqual(len(decoded), 14)

    def test_null_handling(self):
        data = [{"val": None}, {"val": 1}, {"val": None}]
        encoded = zon.encode(data)
        
        self.assertIn("NULL", encoded)
        
        decoded = zon.decode(encoded)
        self.assertIsNone(decoded[0]["val"])
        self.assertEqual(decoded[1]["val"], 1)

    def test_rle_compression(self):
        # Test ZON v3.0 RLE
        # 50 rows of predictable data
        data = [{"id": i, "status": "ok"} for i in range(1, 51)]
        encoded = zon.encode(data, anchor_every=50)
        
        # Check for hybrid schema
        self.assertIn("#{id:R(1,1),status:L}", encoded)
        
        # Check for RLE
        self.assertIn("49x", encoded)
        
        decoded = zon.decode(encoded)
        self.assertEqual(len(decoded), 50)
        self.assertEqual(decoded[0]["id"], 1)

    def test_zmap_compression(self):
        # Test ZON v4.0 Z-Map
        # Repeated non-sequential string
        # Use longer strings to ensure heuristic triggers compression
        # "Sales" (len 5) * 2 = 10 chars. Token %1 (len 2) * 2 = 4 chars. Savings = 6. Cost = 5+5=10. 6 > 10 False.
        # "MarketingDept" (len 13) * 2 = 26 chars. Token %1 (len 2) * 2 = 4 chars. Savings = 22. Cost = 13+5=18. 22 > 18 True.
        data = [{"dept": "Engineering"}, {"dept": "MarketingDept"}, {"dept": "Engineering"}, {"dept": "MarketingDept"}]
        
        encoded = zon.encode(data)
        
        # Check for Z-Map definition (with stricter heuristic, both should still qualify)
        # Token assignment depends on sort order (frequency * (len-2)).
        # Engineering: 2 * (11-2) = 18.
        # MarketingDept: 2 * (13-2) = 22.
        # MarketingDept should be %0, Engineering %1.
        self.assertIn('D %1 = "Engineering"', encoded)
        self.assertIn('D %0 = "MarketingDept"', encoded)
        
        decoded = zon.decode(encoded)
        self.assertEqual(decoded[0]["dept"], "Engineering")

    def test_deep_flattening(self):
        # Test ZON v6.0 Deep Flattening
        # Needs > 2 rows to avoid Inline Mode
        data = [
            {"user": {"profile": {"id": 1, "theme": "dark"}}},
            {"user": {"profile": {"id": 2, "theme": "light"}}},
            {"user": {"profile": {"id": 3, "theme": "dark"}}}
        ]
        encoded = zon.encode(data)
        
        # Check hybrid schema with flattened keys (using '.' not '..')
        self.assertIn("#{user.profile.id:R(1,1)", encoded)
        self.assertIn("user.profile.theme:S}", encoded)
        
        decoded = zon.decode(encoded)
        self.assertEqual(decoded[0]["user"]["profile"]["id"], 1)
        self.assertEqual(decoded[2]["user"]["profile"]["id"], 3)

    def test_inline_mode(self):
        # Test ZON v4.0 Inline Mode (Singleton)
        data = [{"id": 1, "name": "Alice"}]
        encoded = zon.encode(data)
        
        # Check for Inline Marker
        self.assertIn("#ZON v6.0 INLINE", encoded)
        # Check for dense KV
        self.assertIn("id:1", encoded)
        
        decoded = zon.decode(encoded)
        self.assertEqual(len(decoded), 1)
        self.assertEqual(decoded[0]["id"], 1)

    def test_pattern_gas(self):
        # Test ZON v6.0 Pattern Gas
        # ORD-001, ORD-002...
        data = [{"id": f"ORD-{i:03d}"} for i in range(1, 51)]
        encoded = zon.encode(data, anchor_every=50)
        
        # Check hybrid schema with PATTERN
        self.assertIn('#{id:P("ORD-{:03d}",1,1)}', encoded)
        self.assertIn("49x", encoded)
        
        decoded = zon.decode(encoded)
        self.assertEqual(decoded[0]["id"], "ORD-001")
        self.assertEqual(decoded[49]["id"], "ORD-050")

    def test_multiplier_gas(self):
        # Test ZON v6.0 Multiplier Gas
        # 0.52, 0.15...
        data = [{"val": 0.52}, {"val": 0.15}, {"val": 1.00}]
        encoded = zon.encode(data)
        
        # Check hybrid schema with MULTIPLIER
        self.assertIn('#{val:M(0.01)}', encoded)
        self.assertIn("52", encoded)
        
        decoded = zon.decode(encoded)
        self.assertAlmostEqual(decoded[0]["val"], 0.52)

    def test_base62(self):
        # Test ZON v5.0 Base62
        # Large integer
        val = 123456789123
        data = [{"id": val}]
        encoded = zon.encode(data)
        
        # Check for Base62 marker
        self.assertIn("&", encoded)
        
        decoded = zon.decode(encoded)
        self.assertEqual(decoded[0]["id"], val)

if __name__ == "__main__":
    unittest.main()
