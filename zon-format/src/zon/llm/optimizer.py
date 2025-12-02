"""LLM optimizer for optimizing field order to minimize token usage."""

from typing import List, Dict, Any, TYPE_CHECKING
from .token_counter import TokenCounter

if TYPE_CHECKING:
    from ..core.encoder import ZonEncoder

class LLMOptimizer:
    """Optimizes ZON encoding by finding the best field order for token efficiency."""
    
    def __init__(self):
        """Initialize the LLM optimizer."""
        self.tokenizer = TokenCounter()

    def optimize_field_order(self, data: List[Any]) -> List[Any]:
        """Optimize field order in data to minimize token count.
        
        Tests multiple orderings and selects the one producing the smallest encoding.
        
        Args:
            data: List of dict objects to optimize
            
        Returns:
            Data with optimized field order
        """
        if not isinstance(data, list) or len(data) == 0:
            return data

        sample = data[0]
        if not isinstance(sample, dict) or sample is None:
            return data

        fields = list(sample.keys())
        if len(fields) <= 1:
            return data

        from ..core.encoder import ZonEncoder
        encoder = ZonEncoder()
        
        orderings = self._generate_orderings(fields)
        
        best_ordering = fields
        min_tokens = float('inf')

        test_data = data[:min(len(data), 5)]

        for ordering in orderings:
            reordered = self._reorder_data(test_data, ordering)
            encoded = encoder.encode(reordered)
            tokens = self.tokenizer.count(encoded)

            if tokens < min_tokens:
                min_tokens = tokens
                best_ordering = ordering

        return self._reorder_data(data, best_ordering)

    def _reorder_data(self, data: List[Dict[str, Any]], ordering: List[str]) -> List[Dict[str, Any]]:
        """Reorder dict keys according to the specified ordering.
        
        Args:
            data: List of dict objects
            ordering: Desired key order
            
        Returns:
            Data with keys reordered
        """
        result = []
        for row in data:
            new_row = {}
            for field in ordering:
                if field in row:
                    new_row[field] = row[field]
            
            for key in row:
                if key not in ordering:
                    new_row[key] = row[key]
            result.append(new_row)
        return result

    def _generate_orderings(self, fields: List[str]) -> List[List[str]]:
        """Generate different field orderings to test.
        
        Args:
            fields: List of field names
            
        Returns:
            List of different orderings to try
        """
        orderings = []
        orderings.append(list(fields))
        orderings.append(sorted(fields))
        orderings.append(sorted(fields, key=len))
        orderings.append(sorted(fields, key=len, reverse=True))
        return orderings
