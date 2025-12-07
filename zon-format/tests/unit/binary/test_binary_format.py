"""Tests for binary ZON format"""

import struct
import pytest
from zon.binary import encode_binary, decode_binary, MAGIC_HEADER


class TestBinaryBasics:
    """Basic binary encoding/decoding tests"""
    
    def test_magic_header(self):
        """Test that binary output starts with magic header"""
        data = {"test": "value"}
        binary = encode_binary(data)
        assert binary[:4] == MAGIC_HEADER
    
    def test_none_value(self):
        """Test encoding/decoding None"""
        data = None
        binary = encode_binary(data)
        decoded = decode_binary(binary)
        assert decoded is None
    
    def test_boolean_true(self):
        """Test encoding/decoding True"""
        data = True
        binary = encode_binary(data)
        decoded = decode_binary(binary)
        assert decoded is True
    
    def test_boolean_false(self):
        """Test encoding/decoding False"""
        data = False
        binary = encode_binary(data)
        decoded = decode_binary(binary)
        assert decoded is False
    
    def test_small_positive_integer(self):
        """Test encoding/decoding small positive integers"""
        for value in [0, 1, 42, 127]:
            binary = encode_binary(value)
            decoded = decode_binary(binary)
            assert decoded == value
    
    def test_small_negative_integer(self):
        """Test encoding/decoding small negative integers"""
        for value in [-1, -10, -32]:
            binary = encode_binary(value)
            decoded = decode_binary(binary)
            assert decoded == value
    
    def test_medium_integers(self):
        """Test encoding/decoding medium-sized integers"""
        for value in [128, 255, 256, 65535]:
            binary = encode_binary(value)
            decoded = decode_binary(binary)
            assert decoded == value
    
    def test_large_integers(self):
        """Test encoding/decoding large integers"""
        for value in [65536, 1000000, 2147483647]:
            binary = encode_binary(value)
            decoded = decode_binary(binary)
            assert decoded == value
    
    def test_float_values(self):
        """Test encoding/decoding float values"""
        for value in [0.0, 1.5, 3.14159, -2.718]:
            binary = encode_binary(value)
            decoded = decode_binary(binary)
            assert abs(decoded - value) < 1e-10
    
    def test_short_string(self):
        """Test encoding/decoding short strings"""
        data = "Hello"
        binary = encode_binary(data)
        decoded = decode_binary(binary)
        assert decoded == data
    
    def test_medium_string(self):
        """Test encoding/decoding medium strings"""
        data = "Hello, World! " * 10
        binary = encode_binary(data)
        decoded = decode_binary(binary)
        assert decoded == data
    
    def test_unicode_string(self):
        """Test encoding/decoding unicode strings"""
        data = "Hello 世界 🌍"
        binary = encode_binary(data)
        decoded = decode_binary(binary)
        assert decoded == data


class TestBinaryArrays:
    """Test binary encoding of arrays"""
    
    def test_empty_array(self):
        """Test encoding/decoding empty array"""
        data = []
        binary = encode_binary(data)
        decoded = decode_binary(binary)
        assert decoded == data
    
    def test_small_array(self):
        """Test encoding/decoding small array"""
        data = [1, 2, 3]
        binary = encode_binary(data)
        decoded = decode_binary(binary)
        assert decoded == data
    
    def test_mixed_type_array(self):
        """Test encoding/decoding mixed type array"""
        data = [1, "two", 3.0, True, None]
        binary = encode_binary(data)
        decoded = decode_binary(binary)
        assert decoded == data
    
    def test_nested_array(self):
        """Test encoding/decoding nested arrays"""
        data = [[1, 2], [3, 4], [5, 6]]
        binary = encode_binary(data)
        decoded = decode_binary(binary)
        assert decoded == data
    
    def test_large_array(self):
        """Test encoding/decoding large array"""
        data = list(range(100))
        binary = encode_binary(data)
        decoded = decode_binary(binary)
        assert decoded == data


class TestBinaryObjects:
    """Test binary encoding of objects/dicts"""
    
    def test_empty_object(self):
        """Test encoding/decoding empty object"""
        data = {}
        binary = encode_binary(data)
        decoded = decode_binary(binary)
        assert decoded == data
    
    def test_simple_object(self):
        """Test encoding/decoding simple object"""
        data = {"name": "Alice", "age": 30}
        binary = encode_binary(data)
        decoded = decode_binary(binary)
        assert decoded == data
    
    def test_nested_object(self):
        """Test encoding/decoding nested object"""
        data = {
            "user": {
                "name": "Alice",
                "profile": {
                    "age": 30,
                    "city": "NYC"
                }
            }
        }
        binary = encode_binary(data)
        decoded = decode_binary(binary)
        assert decoded == data
    
    def test_object_with_array(self):
        """Test encoding/decoding object with arrays"""
        data = {
            "users": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"}
            ]
        }
        binary = encode_binary(data)
        decoded = decode_binary(binary)
        assert decoded == data
    
    def test_complex_nested_structure(self):
        """Test encoding/decoding complex nested structure"""
        data = {
            "metadata": {
                "version": "1.0",
                "timestamp": 1234567890
            },
            "users": [
                {
                    "id": 1,
                    "name": "Alice",
                    "tags": ["admin", "user"],
                    "active": True
                },
                {
                    "id": 2,
                    "name": "Bob",
                    "tags": ["user"],
                    "active": False
                }
            ],
            "config": {
                "features": {
                    "darkMode": True,
                    "notifications": False
                }
            }
        }
        binary = encode_binary(data)
        decoded = decode_binary(binary)
        assert decoded == data


class TestBinaryCompression:
    """Test binary format compression efficiency"""
    
    def test_smaller_than_json(self):
        """Test that binary format is smaller than JSON"""
        import json
        
        data = {
            "users": [
                {"id": i, "name": f"User{i}", "active": True}
                for i in range(10)
            ]
        }
        
        binary = encode_binary(data)
        json_str = json.dumps(data, separators=(',', ':'))
        
        assert len(binary) < len(json_str.encode('utf-8'))
    
    def test_compression_ratio(self):
        """Test compression ratio for typical data"""
        import json
        
        data = [{"id": i, "value": i * 2} for i in range(50)]
        
        binary = encode_binary(data)
        json_bytes = json.dumps(data, separators=(',', ':')).encode('utf-8')
        
        ratio = len(binary) / len(json_bytes)
        assert ratio < 0.7


class TestBinaryRoundTrip:
    """Test round-trip encoding/decoding"""
    
    def test_all_types_roundtrip(self):
        """Test round-trip for all supported types"""
        test_cases = [
            None,
            True,
            False,
            0,
            42,
            -10,
            3.14,
            "",
            "Hello",
            [],
            [1, 2, 3],
            {},
            {"key": "value"},
            {
                "null": None,
                "bool": True,
                "int": 42,
                "float": 3.14,
                "str": "test",
                "array": [1, 2, 3],
                "obj": {"nested": "value"}
            }
        ]
        
        for data in test_cases:
            binary = encode_binary(data)
            decoded = decode_binary(binary)
            assert decoded == data


class TestBinaryErrors:
    """Test error handling"""
    
    def test_invalid_magic_header(self):
        """Test that invalid magic header raises error"""
        with pytest.raises(ValueError, match="Invalid binary ZON format"):
            decode_binary(b"INVALID")
    
    def test_truncated_data(self):
        """Test that truncated data raises error"""
        data = {"test": "value"}
        binary = encode_binary(data)
        
        with pytest.raises((ValueError, struct.error)):
            decode_binary(binary[:len(binary)//2])
