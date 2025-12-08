"""
Adaptive Encoding API

Provides intelligent format selection based on data characteristics.
"""

from typing import Any, Dict, Optional, Literal, Union
from dataclasses import dataclass

from .encoder import encode, ZonEncoder
from .analyzer import DataComplexityAnalyzer, ComplexityMetrics, AnalysisResult
from ..tools.printer import expand_print


EncodingMode = Literal['compact', 'readable', 'llm-optimized']

@dataclass
class AdaptiveEncodeOptions:
    """Options for adaptive encoding."""
    
    mode: Optional[EncodingMode] = 'compact'
    """Encoding mode (default: 'compact')"""
    
    complexity_threshold: float = 0.6
    """Complexity threshold for auto mode (0.0-1.0)"""
    
    max_nesting_for_table: int = 3
    """Maximum nesting depth for table format"""
    
    indent: int = 2
    """Indentation size for readable mode"""
    
    debug: bool = False
    """Enable detailed analysis logging"""
    
    # Additional encoding options
    enable_dict_compression: Optional[bool] = None
    enable_type_coercion: Optional[bool] = None



@dataclass
class AdaptiveEncodeResult:
    """Result of adaptive encoding with debug information."""
    
    output: str
    """Encoded ZON string"""
    
    metrics: ComplexityMetrics
    """Complexity metrics"""
    
    mode_used: EncodingMode
    """Mode that was used"""
    
    decisions: list
    """Reasons for encoding decisions"""


class AdaptiveEncoder:
    """Adaptive encoder that selects optimal encoding strategy."""
    
    def __init__(self):
        self.analyzer = DataComplexityAnalyzer()
    
    def encode(
        self, 
        data: Any, 
        options: Optional[AdaptiveEncodeOptions] = None
    ) -> Union[str, AdaptiveEncodeResult]:
        """
        Encodes data using adaptive strategy selection.
        
        Args:
            data: Data to encode
            options: Adaptive encoding options
            
        Returns:
            Encoded string or detailed result if debug=True
        """
        if options is None:
            options = AdaptiveEncodeOptions()
        
        mode = options.mode or 'compact'
        decisions = []
        
        # Analyze data
        analysis = self.analyzer.analyze(data)
        metrics = analysis
        
        decisions.append(f"Analyzed data: {analysis.reason}")
        
        # Select encoding options based on mode
        if mode == 'compact':
            encode_options = self._get_compact_options(decisions)
        elif mode == 'readable':
            encode_options = self._get_readable_options(decisions)
        elif mode == 'llm-optimized':
            encode_options = self._get_llm_optimized_options(analysis, decisions)
        else:
            encode_options = {}
        
        # Override with user-provided options if specified
        if options.enable_dict_compression is not None:
            encode_options['enable_dict_compression'] = options.enable_dict_compression
        if options.enable_type_coercion is not None:
            encode_options['enable_type_coercion'] = options.enable_type_coercion
        
        # Create encoder with the selected options
        encoder = ZonEncoder(
            enable_dict_compression=encode_options.get('enable_dict_compression', True),
            enable_type_coercion=encode_options.get('enable_type_coercion', False),
            use_long_booleans=encode_options.get('use_long_booleans', False)
        )
        
        # Encode data
        output = encoder.encode(data)
        
        # Apply formatting for readable mode
        # Note: Pretty-printed output may not round-trip through decoder
        # due to decoder limitations with whitespace after colons
        if mode == 'readable' and not output.startswith('@'):
            output = self._expand_print(output, options.indent)
        
        mode_used = mode
        
        if options.debug:
            return AdaptiveEncodeResult(
                output=output,
                metrics=metrics,
                mode_used=mode_used,
                decisions=decisions
            )
        
        return output
    
    def _get_compact_options(self, decisions: list) -> Dict[str, Any]:
        """Gets encoding options for compact mode."""
        decisions.append('Compact mode: maximum compression enabled')
        return {
            'enable_dict_compression': True,
            'enable_type_coercion': False  # Use T/F for max compression
        }
    
    def _get_readable_options(self, decisions: list) -> Dict[str, Any]:
        """Gets encoding options for readable mode."""
        decisions.append('Readable mode: optimizing for human readability')
        return {
            'enable_dict_compression': False,
            'enable_type_coercion': False,
            'use_long_booleans': True  # Use true/false for readability
        }
    
    def _get_llm_optimized_options(
        self, 
        analysis: AnalysisResult, 
        decisions: list
    ) -> Dict[str, Any]:
        """Gets encoding options for LLM-optimized mode."""
        decisions.append('LLM-optimized mode: balancing tokens and clarity')
        
        # For LLMs, prioritize clarity over compression
        return {
            'enable_dict_compression': False,  # Show actual values
            'enable_type_coercion': False,     # Keep original types
            'use_long_booleans': True          # Use true/false for clarity
        }
    
    def _expand_print(self, output: str, indent: int = 2) -> str:
        """Expands output for readable mode with indentation."""
        return expand_print(output, indent)


# Global adaptive encoder instance
_global_adaptive_encoder = AdaptiveEncoder()


def encode_adaptive(
    data: Any,
    options: Optional[AdaptiveEncodeOptions] = None,
    **kwargs
) -> Union[str, AdaptiveEncodeResult]:
    """
    Encodes data with adaptive strategy selection.
    
    Args:
        data: Data to encode
        options: Adaptive encoding options
        **kwargs: Additional options passed as keywords
        
    Returns:
        Encoded ZON string or detailed result if debug=True
        
    Examples:
        >>> # Compact mode (default)
        >>> output = encode_adaptive(data)
        
        >>> # Explicit mode
        >>> output = encode_adaptive(data, AdaptiveEncodeOptions(mode='readable'))
        
        >>> # With debugging
        >>> result = encode_adaptive(data, AdaptiveEncodeOptions(debug=True))
        >>> print(result.decisions)
    """
    if options is None:
        options = AdaptiveEncodeOptions(**kwargs)
    return _global_adaptive_encoder.encode(data, options)


def recommend_mode(data: Any) -> Dict[str, Any]:
    """
    Analyzes data and recommends optimal encoding mode.
    
    Args:
        data: Data to analyze
        
    Returns:
        Dictionary with recommended mode, confidence, and reason
        
    Example:
        >>> recommendation = recommend_mode(my_data)
        >>> print(f"Use {recommendation['mode']} mode: {recommendation['reason']}")
    """
    analysis = _global_adaptive_encoder.analyzer.analyze(data)
    
    # Map recommendations to modes
    mode_map = {
        'table': 'compact',
        'inline': 'readable',
        'json': 'llm-optimized',
        'mixed': 'llm-optimized'
    }
    
    recommended_mode = mode_map.get(analysis.recommendation, 'compact')
    
    return {
        'mode': recommended_mode,
        'confidence': analysis.confidence,
        'reason': analysis.reason,
        'metrics': {
            'nesting': analysis.nesting,
            'irregularity': analysis.irregularity,
            'field_count': analysis.field_count,
            'array_size': analysis.array_size
        }
    }
