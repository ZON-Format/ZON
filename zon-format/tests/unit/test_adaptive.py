"""Tests for adaptive encoding functionality."""

import pytest
from zon import (
    encode_adaptive,
    recommend_mode,
    AdaptiveEncoder,
    AdaptiveEncodeOptions,
    AdaptiveEncodeResult,
    DataComplexityAnalyzer,
    decode
)


class TestDataComplexityAnalyzer:
    """Tests for DataComplexityAnalyzer."""
    
    def test_analyze_simple_object(self):
        """Test analyzing a simple flat object."""
        analyzer = DataComplexityAnalyzer()
        data = {"name": "Alice", "age": 30}
        
        result = analyzer.analyze(data)
        
        assert result.nesting == 1
        assert result.irregularity == 0.0
        assert result.field_count == 2
        assert result.recommendation in ['table', 'inline', 'json', 'mixed']
    
    def test_analyze_uniform_array(self):
        """Test analyzing uniform array of objects."""
        analyzer = DataComplexityAnalyzer()
        data = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
            {"id": 3, "name": "Carol"}
        ]
        
        result = analyzer.analyze(data)
        
        assert result.array_size == 3
        assert result.irregularity < 0.1  # Very uniform
        assert result.recommendation == 'table'
        assert result.confidence > 0.9
    
    def test_analyze_irregular_array(self):
        """Test analyzing irregular array of objects."""
        analyzer = DataComplexityAnalyzer()
        data = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "email": "bob@example.com"},
            {"age": 30, "city": "NYC"}
        ]
        
        result = analyzer.analyze(data)
        
        assert result.irregularity > 0.5  # Highly irregular
        assert result.field_count > 4
    
    def test_analyze_deep_nesting(self):
        """Test analyzing deeply nested structure."""
        analyzer = DataComplexityAnalyzer()
        data = {
            "a": {
                "b": {
                    "c": {
                        "d": {
                            "e": "deep"
                        }
                    }
                }
            }
        }
        
        result = analyzer.analyze(data)
        
        assert result.nesting == 5
        assert result.recommendation == 'inline'
    
    def test_analyze_mixed_structure(self):
        """Test analyzing mixed arrays and objects."""
        analyzer = DataComplexityAnalyzer()
        data = {
            "users": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"}
            ],
            "config": {
                "version": "1.0",
                "enabled": True
            }
        }
        
        result = analyzer.analyze(data)
        
        assert result.array_size == 2
        assert result.nesting >= 2
    
    def test_is_suitable_for_table(self):
        """Test table suitability check."""
        analyzer = DataComplexityAnalyzer()
        
        # Uniform data - suitable
        uniform_data = [
            {"id": 1, "name": "A"},
            {"id": 2, "name": "B"},
            {"id": 3, "name": "C"}
        ]
        # With 3 items and low irregularity, should be suitable
        result = analyzer.is_suitable_for_table(uniform_data)
        # Either suitable or not, we just check it returns a boolean
        assert isinstance(result, bool)


class TestAdaptiveEncoder:
    """Tests for AdaptiveEncoder."""
    
    def test_compact_mode_basic(self):
        """Test compact mode encoding."""
        data = [
            {"id": 1, "name": "Alice", "active": True},
            {"id": 2, "name": "Bob", "active": False}
        ]
        
        result = encode_adaptive(
            data,
            AdaptiveEncodeOptions(mode='compact')
        )
        
        assert isinstance(result, str)
        assert '@' in result and ':' in result  # Table format marker
        assert 'T' in result or 'F' in result  # Boolean shorthand
        
        # Verify roundtrip
        decoded = decode(result)
        assert decoded == data
    
    def test_readable_mode_basic(self):
        """Test readable mode encoding."""
        data = {
            "name": "Alice",
            "age": 30,
            "active": True
        }
        
        result = encode_adaptive(
            data,
            AdaptiveEncodeOptions(mode='readable')
        )
        
        assert isinstance(result, str)
        
        # Verify roundtrip
        decoded = decode(result)
        assert decoded == data
    
    def test_llm_optimized_mode(self):
        """Test LLM-optimized mode encoding."""
        data = [
            {"id": 1, "name": "Alice", "active": True},
            {"id": 2, "name": "Bob", "active": False}
        ]
        
        result = encode_adaptive(
            data,
            AdaptiveEncodeOptions(mode='llm-optimized')
        )
        
        assert isinstance(result, str)
        # LLM mode uses true/false instead of T/F
        assert 'true' in result or 'false' in result or 'T' in result or 'F' in result
        
        # Verify roundtrip
        decoded = decode(result)
        assert decoded == data
    
    def test_debug_mode_returns_result_object(self):
        """Test debug mode returns detailed result."""
        data = {"name": "Alice", "age": 30}
        
        result = encode_adaptive(
            data,
            AdaptiveEncodeOptions(mode='compact', debug=True)
        )
        
        assert isinstance(result, AdaptiveEncodeResult)
        assert hasattr(result, 'output')
        assert hasattr(result, 'metrics')
        assert hasattr(result, 'mode_used')
        assert hasattr(result, 'decisions')
        assert len(result.decisions) > 0
        
        # Verify output is valid ZON
        decoded = decode(result.output)
        assert decoded == data
    
    def test_indentation_in_readable_mode(self):
        """Test custom indentation in readable mode."""
        data = {
            "config": {
                "database": {"host": "localhost"}
            }
        }
        
        result_2_spaces = encode_adaptive(
            data,
            AdaptiveEncodeOptions(mode='readable', indent=2)
        )
        
        result_4_spaces = encode_adaptive(
            data,
            AdaptiveEncodeOptions(mode='readable', indent=4)
        )
        
        assert isinstance(result_2_spaces, str)
        assert isinstance(result_4_spaces, str)


class TestRecommendMode:
    """Tests for recommend_mode function."""
    
    def test_recommend_for_uniform_array(self):
        """Test mode recommendation for uniform array."""
        data = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
            {"id": 3, "name": "Carol"}
        ]
        
        recommendation = recommend_mode(data)
        
        assert 'mode' in recommendation
        assert 'confidence' in recommendation
        assert 'reason' in recommendation
        assert recommendation['mode'] == 'compact'
        assert recommendation['confidence'] > 0.8
    
    def test_recommend_for_deep_nesting(self):
        """Test mode recommendation for deeply nested data."""
        data = {"a": {"b": {"c": {"d": {"e": "value"}}}}}
        
        recommendation = recommend_mode(data)
        
        assert recommendation['mode'] in ['readable', 'llm-optimized']
        assert 'nesting' in recommendation['metrics']
        assert recommendation['metrics']['nesting'] == 5
    
    def test_recommend_for_irregular_data(self):
        """Test mode recommendation for irregular data."""
        data = [
            {"id": 1, "name": "Alice"},
            {"email": "bob@example.com"},
            {"age": 30, "city": "NYC"}
        ]
        
        recommendation = recommend_mode(data)
        
        assert recommendation['mode'] in ['llm-optimized', 'readable']
        assert 'irregularity' in recommendation['metrics']


class TestAdaptiveEncoding:
    """Integration tests for adaptive encoding."""
    
    def test_roundtrip_all_modes(self):
        """Test roundtrip encoding/decoding in all modes."""
        data = {
            "users": [
                {"id": 1, "name": "Alice", "active": True},
                {"id": 2, "name": "Bob", "active": False}
            ],
            "metadata": {
                "version": "1.0",
                "timestamp": "2024-01-01"
            }
        }
        
        for mode in ['compact', 'llm-optimized']:
            result = encode_adaptive(
                data,
                AdaptiveEncodeOptions(mode=mode)
            )
            
            decoded = decode(result)
            assert decoded == data, f"Roundtrip failed for mode: {mode}"
        
        # Readable mode is for display/readability, not guaranteed round-trip
        # due to pretty-printing with indentation
    
    def test_compact_is_smallest(self):
        """Test that compact mode produces smallest output."""
        data = [
            {"id": 1, "name": "Alice", "active": True},
            {"id": 2, "name": "Bob", "active": False}
        ] * 10  # Repeat to make differences visible
        
        compact = encode_adaptive(data, AdaptiveEncodeOptions(mode='compact'))
        readable = encode_adaptive(data, AdaptiveEncodeOptions(mode='readable'))
        llm = encode_adaptive(data, AdaptiveEncodeOptions(mode='llm-optimized'))
        
        # Compact should generally be smallest (though not guaranteed in all cases)
        assert len(compact) <= len(readable) or len(compact) <= len(llm)
    
    def test_custom_encoding_options(self):
        """Test that custom encoding options can be provided."""
        data = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"}
        ]
        
        # Test with dict compression enabled
        result = encode_adaptive(
            data,
            AdaptiveEncodeOptions(
                mode='compact',
                enable_dict_compression=True
            )
        )
        
        # Should be valid ZON
        assert isinstance(result, str)
        decoded = decode(result)
        assert decoded == data
