"""
Data Complexity Analyzer for Adaptive Encoding

Analyzes data structures to determine optimal encoding strategies.
"""

from typing import Any, Dict, List, Set, Tuple, Literal
from dataclasses import dataclass


@dataclass
class ComplexityMetrics:
    """Complexity metrics for data structures."""
    
    nesting: int
    """Maximum nesting depth in the data structure"""
    
    irregularity: float
    """Irregularity score (0.0 = uniform, 1.0 = highly irregular)"""
    
    field_count: int
    """Total number of unique fields across all objects"""
    
    array_size: int
    """Size of largest array in the structure"""
    
    array_density: float
    """Proportion of arrays vs objects"""
    
    avg_fields_per_object: float
    """Average fields per object"""


@dataclass
class AnalysisResult(ComplexityMetrics):
    """Analysis result with encoding recommendation."""
    
    recommendation: Literal['table', 'inline', 'json', 'mixed']
    """Recommended encoding strategy"""
    
    confidence: float
    """Confidence in recommendation (0.0-1.0)"""
    
    reason: str
    """Reasoning for the recommendation"""


class DataComplexityAnalyzer:
    """Analyzes data complexity to guide encoding decisions."""
    
    def analyze(self, data: Any) -> AnalysisResult:
        """
        Analyzes a data structure and returns complexity metrics.
        
        Args:
            data: Data to analyze
            
        Returns:
            Complexity metrics and encoding recommendation
        """
        metrics = self._calculate_metrics(data)
        recommendation = self._get_recommendation(metrics)
        
        return AnalysisResult(
            nesting=metrics.nesting,
            irregularity=metrics.irregularity,
            field_count=metrics.field_count,
            array_size=metrics.array_size,
            array_density=metrics.array_density,
            avg_fields_per_object=metrics.avg_fields_per_object,
            recommendation=recommendation['recommendation'],
            confidence=recommendation['confidence'],
            reason=recommendation['reason']
        )
    
    def _calculate_metrics(self, data: Any) -> ComplexityMetrics:
        """Calculates complexity metrics for data."""
        stats = {
            'max_nesting': 0,
            'all_keys': set(),
            'key_sets': [],
            'largest_array': 0,
            'array_count': 0,
            'object_count': 0,
            'field_counts': []
        }
        
        self._traverse(data, 1, stats)
        
        # Calculate irregularity
        irregularity = self._calculate_irregularity(stats['key_sets'])
        
        # Calculate array density
        total = stats['array_count'] + stats['object_count']
        array_density = stats['array_count'] / total if total > 0 else 0
        
        # Calculate average fields per object
        avg_fields = (
            sum(stats['field_counts']) / len(stats['field_counts'])
            if stats['field_counts'] else 0
        )
        
        return ComplexityMetrics(
            nesting=stats['max_nesting'],
            irregularity=irregularity,
            field_count=len(stats['all_keys']),
            array_size=stats['largest_array'],
            array_density=array_density,
            avg_fields_per_object=avg_fields
        )
    
    def _traverse(self, data: Any, depth: int, stats: Dict) -> None:
        """Traverses data structure to collect statistics."""
        if isinstance(data, (dict, list)) and data is not None:
            stats['max_nesting'] = max(stats['max_nesting'], depth)
        
        if isinstance(data, list):
            stats['array_count'] += 1
            stats['largest_array'] = max(stats['largest_array'], len(data))
            
            for item in data:
                self._traverse(item, depth + 1, stats)
                
        elif isinstance(data, dict):
            stats['object_count'] += 1
            
            keys = set(data.keys())
            stats['key_sets'].append(keys)
            stats['field_counts'].append(len(keys))
            
            for key in keys:
                stats['all_keys'].add(key)
            
            for value in data.values():
                self._traverse(value, depth + 1, stats)
    
    def _calculate_irregularity(self, key_sets: List[Set[str]]) -> float:
        """
        Calculates schema irregularity score.
        Higher score = more variation in object shapes.
        """
        if len(key_sets) <= 1:
            return 0.0
        
        total_overlap = 0.0
        comparisons = 0
        
        for i in range(len(key_sets)):
            for j in range(i + 1, len(key_sets)):
                keys1 = key_sets[i]
                keys2 = key_sets[j]
                
                shared = len(keys1 & keys2)
                union = len(keys1 | keys2)
                
                similarity = shared / union if union > 0 else 1.0
                
                total_overlap += similarity
                comparisons += 1
        
        if comparisons == 0:
            return 0.0
        
        avg_similarity = total_overlap / comparisons
        return 1.0 - avg_similarity
    
    def _get_recommendation(self, metrics: ComplexityMetrics) -> Dict[str, Any]:
        """Determines encoding recommendation based on metrics."""
        
        # Deep nesting favors inline format
        if metrics.nesting > 4:
            return {
                'recommendation': 'inline',
                'confidence': 0.9,
                'reason': f'Deep nesting ({metrics.nesting} levels) favors inline format for readability'
            }
        
        # High irregularity makes table format inefficient
        if metrics.irregularity > 0.7:
            return {
                'recommendation': 'json',
                'confidence': 0.85,
                'reason': f'High irregularity ({metrics.irregularity * 100:.0f}%) makes table format inefficient'
            }
        
        # Large uniform arrays are ideal for table format
        if metrics.array_size >= 3 and metrics.irregularity < 0.3:
            return {
                'recommendation': 'table',
                'confidence': 0.95,
                'reason': f'Large uniform array ({metrics.array_size} items, {metrics.irregularity * 100:.0f}% irregularity) is ideal for table format'
            }
        
        # Mixed structures benefit from hybrid approach
        if metrics.nesting > 2 and metrics.array_density > 0.3:
            return {
                'recommendation': 'mixed',
                'confidence': 0.7,
                'reason': 'Mixed structure with nested arrays benefits from hybrid approach'
            }
        
        # Default to table format
        return {
            'recommendation': 'table',
            'confidence': 0.6,
            'reason': 'Standard structure suitable for table format'
        }
    
    def is_suitable_for_table(self, data: Any) -> bool:
        """Checks if data is suitable for table encoding."""
        analysis = self.analyze(data)
        return analysis.recommendation == 'table' and analysis.confidence > 0.7
    
    def get_complexity_threshold(
        self, 
        mode: Literal['aggressive', 'balanced', 'conservative'] = 'balanced'
    ) -> float:
        """Gets optimal complexity threshold for mode selection."""
        thresholds = {
            'aggressive': 0.8,   # Only switch away from table for very irregular data
            'conservative': 0.4,  # More readily use inline/json formats
            'balanced': 0.6
        }
        return thresholds[mode]


# Global analyzer instance
global_analyzer = DataComplexityAnalyzer()
