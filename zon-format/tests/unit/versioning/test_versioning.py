"""Tests for ZON versioning system"""

import pytest
from zon.versioning import (
    embed_version,
    extract_version,
    strip_version,
    compare_versions,
    is_compatible,
    ZonDocumentMetadata
)


class TestVersionEmbedding:
    """Test version embedding"""
    
    def test_embed_version_basic(self):
        """Test basic version embedding"""
        data = {"users": [{"id": 1, "name": "Alice"}]}
        versioned = embed_version(data, "1.0.0")
        
        assert '__zon_meta' in versioned
        assert versioned['__zon_meta']['version'] == "1.0.0"
        assert 'users' in versioned
        assert versioned['users'] == data['users']
    
    def test_embed_version_with_schema_id(self):
        """Test embedding with schema ID"""
        data = {"test": "value"}
        versioned = embed_version(data, "2.0.0", schema_id="test-schema")
        
        assert versioned['__zon_meta']['version'] == "2.0.0"
        assert versioned['__zon_meta']['schemaId'] == "test-schema"
    
    def test_embed_version_with_encoding(self):
        """Test embedding with encoding type"""
        data = {"test": "value"}
        versioned = embed_version(data, "1.0.0", encoding="zon-binary")
        
        assert versioned['__zon_meta']['encoding'] == "zon-binary"
    
    def test_embed_version_adds_timestamp(self):
        """Test that timestamp is added"""
        data = {"test": "value"}
        versioned = embed_version(data, "1.0.0")
        
        assert 'timestamp' in versioned['__zon_meta']
        assert isinstance(versioned['__zon_meta']['timestamp'], int)
    
    def test_embed_version_rejects_non_dict(self):
        """Test that non-dict data is rejected"""
        with pytest.raises(TypeError):
            embed_version([1, 2, 3], "1.0.0")
        
        with pytest.raises(TypeError):
            embed_version("string", "1.0.0")


class TestVersionExtraction:
    """Test version extraction"""
    
    def test_extract_version_basic(self):
        """Test basic version extraction"""
        data = {"users": []}
        versioned = embed_version(data, "1.5.0", "user-schema")
        
        meta = extract_version(versioned)
        
        assert meta is not None
        assert meta.version == "1.5.0"
        assert meta.schema_id == "user-schema"
    
    def test_extract_version_from_unversioned(self):
        """Test extracting from unversioned data returns None"""
        data = {"test": "value"}
        meta = extract_version(data)
        
        assert meta is None
    
    def test_extract_version_from_invalid(self):
        """Test extracting from invalid data"""
        assert extract_version(None) is None
        assert extract_version([1, 2, 3]) is None
        assert extract_version("string") is None
    
    def test_extract_version_preserves_encoding(self):
        """Test that encoding is preserved"""
        data = {"test": "value"}
        versioned = embed_version(data, "1.0.0", encoding="zon-binary")
        
        meta = extract_version(versioned)
        assert meta.encoding == "zon-binary"


class TestVersionStripping:
    """Test version stripping"""
    
    def test_strip_version_removes_metadata(self):
        """Test that strip_version removes metadata"""
        data = {"users": [{"id": 1}]}
        versioned = embed_version(data, "1.0.0")
        stripped = strip_version(versioned)
        
        assert '__zon_meta' not in stripped
        assert stripped == data
    
    def test_strip_version_preserves_data(self):
        """Test that data is preserved after stripping"""
        data = {
            "users": [{"id": 1, "name": "Alice"}],
            "config": {"version": "app-1.0"}
        }
        versioned = embed_version(data, "2.0.0")
        stripped = strip_version(versioned)
        
        assert stripped == data
    
    def test_strip_version_from_unversioned(self):
        """Test stripping from unversioned data"""
        data = {"test": "value"}
        stripped = strip_version(data)
        
        assert stripped == data


class TestVersionComparison:
    """Test version comparison"""
    
    def test_compare_versions_equal(self):
        """Test comparing equal versions"""
        assert compare_versions("1.0.0", "1.0.0") == 0
        assert compare_versions("2.5.3", "2.5.3") == 0
    
    def test_compare_versions_less_than(self):
        """Test comparing when first < second"""
        assert compare_versions("1.0.0", "2.0.0") == -1
        assert compare_versions("1.5.0", "1.6.0") == -1
        assert compare_versions("1.0.5", "1.0.6") == -1
    
    def test_compare_versions_greater_than(self):
        """Test comparing when first > second"""
        assert compare_versions("2.0.0", "1.0.0") == 1
        assert compare_versions("1.6.0", "1.5.0") == 1
        assert compare_versions("1.0.6", "1.0.5") == 1
    
    def test_compare_versions_major_takes_precedence(self):
        """Test that major version takes precedence"""
        assert compare_versions("2.0.0", "1.9.9") == 1
        assert compare_versions("1.0.0", "2.0.0") == -1


class TestVersionCompatibility:
    """Test version compatibility"""
    
    def test_is_compatible_same_major_higher_minor(self):
        """Test compatibility with same major, higher minor"""
        assert is_compatible("1.3.0", "1.2.0") is True
        assert is_compatible("1.5.0", "1.0.0") is True
    
    def test_is_compatible_same_version(self):
        """Test compatibility with same version"""
        assert is_compatible("1.2.0", "1.2.0") is True
    
    def test_not_compatible_lower_minor(self):
        """Test not compatible with lower minor version"""
        assert is_compatible("1.2.0", "1.3.0") is False
    
    def test_not_compatible_different_major(self):
        """Test not compatible with different major version"""
        assert is_compatible("2.0.0", "1.9.0") is False
        assert is_compatible("1.0.0", "2.0.0") is False
    
    def test_is_compatible_patch_version(self):
        """Test compatibility with patch versions"""
        assert is_compatible("1.2.5", "1.2.3") is True
        assert is_compatible("1.2.3", "1.2.5") is False


class TestZonDocumentMetadata:
    """Test ZonDocumentMetadata class"""
    
    def test_metadata_to_dict(self):
        """Test converting metadata to dict"""
        meta = ZonDocumentMetadata(
            version="1.0.0",
            schema_id="test",
            encoding="zon",
            timestamp=1234567890
        )
        
        d = meta.to_dict()
        assert d['version'] == "1.0.0"
        assert d['schemaId'] == "test"
        assert d['encoding'] == "zon"
        assert d['timestamp'] == 1234567890
    
    def test_metadata_from_dict(self):
        """Test creating metadata from dict"""
        d = {
            'version': '2.0.0',
            'schemaId': 'user-profile',
            'encoding': 'zon-binary',
            'timestamp': 9876543210
        }
        
        meta = ZonDocumentMetadata.from_dict(d)
        assert meta.version == '2.0.0'
        assert meta.schema_id == 'user-profile'
        assert meta.encoding == 'zon-binary'
        assert meta.timestamp == 9876543210
    
    def test_metadata_roundtrip(self):
        """Test metadata roundtrip to_dict -> from_dict"""
        original = ZonDocumentMetadata(
            version="1.5.0",
            schema_id="test-schema",
            custom={"author": "Alice"}
        )
        
        d = original.to_dict()
        restored = ZonDocumentMetadata.from_dict(d)
        
        assert restored.version == original.version
        assert restored.schema_id == original.schema_id
