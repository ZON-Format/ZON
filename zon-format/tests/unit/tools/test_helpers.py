"""Tests for ZON tools helpers"""

import pytest
from zon.tools import size, compare_formats, infer_schema, analyze, compare, is_safe


class TestSize:
    """Test size calculation"""
    
    def test_size_zon(self):
        """Test ZON size calculation"""
        data = {"name": "Alice", "age": 30}
        zon_size = size(data, 'zon')
        assert zon_size > 0
    
    def test_size_binary(self):
        """Test binary size calculation"""
        data = {"name": "Alice", "age": 30}
        binary_size = size(data, 'binary')
        assert binary_size > 0
    
    def test_size_json(self):
        """Test JSON size calculation"""
        data = {"name": "Alice", "age": 30}
        json_size = size(data, 'json')
        assert json_size > 0
    
    def test_binary_smaller_than_json(self):
        """Test that binary is typically smaller than JSON"""
        data = [{"id": i, "value": i * 2} for i in range(20)]
        
        binary_size = size(data, 'binary')
        json_size = size(data, 'json')
        
        assert binary_size < json_size


class TestCompareFormats:
    """Test format comparison"""
    
    def test_compare_formats_structure(self):
        """Test compare_formats returns correct structure"""
        data = {"test": "value"}
        result = compare_formats(data)
        
        assert 'zon' in result
        assert 'binary' in result
        assert 'json' in result
        assert 'savings' in result
    
    def test_compare_formats_savings(self):
        """Test savings calculations"""
        data = [{"id": i, "name": f"User{i}"} for i in range(10)]
        result = compare_formats(data)
        
        assert 'zon_vs_json' in result['savings']
        assert 'binary_vs_json' in result['savings']
        assert 'binary_vs_zon' in result['savings']
    
    def test_compare_formats_all_positive_sizes(self):
        """Test all sizes are positive"""
        data = {"users": [{"id": 1}]}
        result = compare_formats(data)
        
        assert result['zon'] > 0
        assert result['binary'] > 0
        assert result['json'] > 0


class TestInferSchema:
    """Test schema inference"""
    
    def test_infer_null(self):
        """Test inferring null type"""
        schema = infer_schema(None)
        assert schema['type'] == 'null'
    
    def test_infer_boolean(self):
        """Test inferring boolean type"""
        schema = infer_schema(True)
        assert schema['type'] == 'boolean'
    
    def test_infer_integer(self):
        """Test inferring integer type"""
        schema = infer_schema(42)
        assert schema['type'] == 'integer'
    
    def test_infer_float(self):
        """Test inferring float type"""
        schema = infer_schema(3.14)
        assert schema['type'] == 'number'
    
    def test_infer_string(self):
        """Test inferring string type"""
        schema = infer_schema("hello")
        assert schema['type'] == 'string'
    
    def test_infer_array(self):
        """Test inferring array type"""
        schema = infer_schema([1, 2, 3])
        assert schema['type'] == 'array'
        assert 'items' in schema
    
    def test_infer_empty_array(self):
        """Test inferring empty array"""
        schema = infer_schema([])
        assert schema['type'] == 'array'
        assert schema['items']['type'] == 'any'
    
    def test_infer_object(self):
        """Test inferring object type"""
        schema = infer_schema({"name": "Alice", "age": 30})
        assert schema['type'] == 'object'
        assert 'properties' in schema
        assert 'name' in schema['properties']
        assert 'age' in schema['properties']
    
    def test_infer_nested_object(self):
        """Test inferring nested object"""
        data = {
            "user": {
                "name": "Alice",
                "age": 30
            }
        }
        schema = infer_schema(data)
        
        assert schema['type'] == 'object'
        assert schema['properties']['user']['type'] == 'object'


class TestAnalyze:
    """Test data analysis"""
    
    def test_analyze_depth(self):
        """Test depth calculation"""
        data = {"a": {"b": {"c": "value"}}}
        stats = analyze(data)
        
        assert stats['depth'] >= 3
    
    def test_analyze_field_count(self):
        """Test field count"""
        data = {"a": 1, "b": 2, "c": {"d": 3}}
        stats = analyze(data)
        
        assert stats['field_count'] >= 4
    
    def test_analyze_type(self):
        """Test type detection"""
        data = {"test": "value"}
        stats = analyze(data)
        
        assert stats['type'] == 'dict'


class TestCompare:
    """Test data comparison"""
    
    def test_compare_equal(self):
        """Test comparing equal data"""
        data1 = {"name": "Alice"}
        data2 = {"name": "Alice"}
        
        result = compare(data1, data2)
        assert result['equal'] is True
    
    def test_compare_not_equal(self):
        """Test comparing different data"""
        data1 = {"name": "Alice"}
        data2 = {"name": "Bob"}
        
        result = compare(data1, data2)
        assert result['equal'] is False
    
    def test_compare_types(self):
        """Test type comparison"""
        data1 = {"test": "value"}
        data2 = [1, 2, 3]
        
        result = compare(data1, data2)
        assert result['data1_type'] == 'dict'
        assert result['data2_type'] == 'list'


class TestIsSafe:
    """Test safety checks"""
    
    def test_is_safe_simple_data(self):
        """Test safe simple data"""
        data = {"name": "Alice", "age": 30}
        result = is_safe(data)
        
        assert result['safe'] is True
    
    def test_is_safe_deep_nesting(self):
        """Test unsafe deep nesting"""
        data = {"a": {"b": {"c": {"d": {"e": {"f": {"g": {"h": {"i": {"j": {"k": "deep"}}}}}}}}}}}
        
        result = is_safe(data, max_depth=5)
        assert result['safe'] is False
    
    def test_is_safe_returns_depth(self):
        """Test that depth is returned"""
        data = {"test": "value"}
        result = is_safe(data)
        
        assert 'depth' in result
        assert 'max_depth' in result
    
    def test_is_safe_returns_size(self):
        """Test that size is returned"""
        data = {"test": "value"}
        result = is_safe(data)
        
        assert 'size' in result
        assert 'max_size' in result
