"""ZON (Zstandard Object Notation) - Token-efficient data format for LLMs.

This package provides encoding and decoding functionality for the ZON format,
optimized for minimal token usage in LLM interactions while maintaining full
data fidelity and type safety.

Main components:
    - encode/decode: Core encoding and decoding functions
    - ZonEncoder/ZonDecoder: Class-based codec interfaces
    - ZonStreamEncoder/ZonStreamDecoder: Streaming codec for large data
    - LLMOptimizer: Optimize encodings for specific LLM contexts
    - TokenCounter: Count tokens in ZON-encoded data
    - TypeInferrer: Infer and validate data types
    - SparseMode: Enumeration of sparse encoding strategies
"""

from .core.encoder import encode, encode_llm, ZonEncoder
from .core.decoder import decode, ZonDecoder
from .core.stream import ZonStreamEncoder, ZonStreamDecoder
from .llm.optimizer import LLMOptimizer
from .llm.token_counter import TokenCounter
from .schema.inference import TypeInferrer
from .core.types import SparseMode
from .core.exceptions import ZonDecodeError, ZonEncodeError
from .schema.schema import zon, validate, ZonResult, ZonIssue, ZonSchema

__version__ = "1.1.0"

__all__ = [
    "encode", 
    "encode_llm",
    "ZonEncoder",
    "decode", 
    "ZonDecoder",
    "ZonStreamEncoder",
    "ZonStreamDecoder",
    "LLMOptimizer",
    "TokenCounter",
    "TypeInferrer",
    "SparseMode",
    "ZonDecodeError", 
    "ZonEncodeError",
    "zon",
    "validate",
    "ZonResult",
    "ZonIssue",
    "ZonSchema",
    "__version__"
]
