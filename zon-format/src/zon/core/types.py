"""Type definitions for the ZON format library."""

from enum import Enum
from typing import TypedDict, Optional

class SparseMode(Enum):
    """Enumeration of sparse encoding strategies for optimizing repeated data.
    
    Attributes:
        NONE: No sparse encoding applied
        BASIC: Basic run-length encoding for repeated values
        HIERARCHICAL: Hierarchical encoding preserving nested structure
        DELTA: Delta encoding for sequential numeric data
        HYBRID: Combination of multiple sparse encoding strategies
    """
    NONE = 'none'
    BASIC = 'basic'
    HIERARCHICAL = 'hierarchical'
    DELTA = 'delta'
    HYBRID = 'hybrid'

class ZonType(TypedDict, total=False):
    """Type information dictionary for ZON type inference and coercion.
    
    Attributes:
        type: Inferred type name (e.g., 'int', 'float', 'bool', 'str')
        coercible: Whether the value can be safely coerced to this type
        original: Original string representation before coercion
        confidence: Confidence score for the type inference (0.0 to 1.0)
    """
    type: str
    coercible: bool
    original: Optional[str]
    confidence: Optional[float]
