from typing import List, Dict, Any, Optional
import math
from ..core.encoder import encode, ZonEncoder

class ZonSplitter:
    """
    Splits large datasets into ZON-encoded chunks respecting token limits.
    """
    def __init__(self, max_tokens: int, overlap: int = 0, token_ratio: float = 4.0):
        """
        Initialize the splitter.
        
        Args:
            max_tokens: Maximum tokens per chunk.
            overlap: Number of items to overlap between chunks.
            token_ratio: Estimated characters per token (default 4.0).
        """
        self.max_chars = int(max_tokens * token_ratio)
        self.overlap = overlap
        self.encoder = ZonEncoder()

    def split(self, data: List[Any]) -> Dict[str, Any]:
        """
        Splits a list of data into ZON-encoded chunks.
        
        Args:
            data: List of items to split.
            
        Returns:
            Dict containing 'chunks' (list of strings) and 'metadata'.
        """
        if not isinstance(data, list) or not data:
            return {
                'chunks': [],
                'metadata': {
                    'total_chunks': 0,
                    'total_tokens': 0,
                    'chunk_sizes': []
                }
            }

        chunks: List[str] = []
        chunk_sizes: List[int] = []
        current_chunk_items: List[Any] = []
        total_tokens = 0

        def estimate_tokens(text: str) -> int:
            return math.ceil(len(text) / 4)

        for item in data:
            candidate_items = current_chunk_items + [item]
            encoded = self.encoder.encode(candidate_items)

            if len(encoded) > self.max_chars:
                if current_chunk_items:
                    chunk_encoded = self.encoder.encode(current_chunk_items)
                    chunks.append(chunk_encoded)
                    tokens = estimate_tokens(chunk_encoded)
                    chunk_sizes.append(tokens)
                    total_tokens += tokens

                    overlap_items = current_chunk_items[-self.overlap:] if self.overlap > 0 else []
                    current_chunk_items = overlap_items + [item]
                else:
                    chunk_encoded = self.encoder.encode([item])
                    chunks.append(chunk_encoded)
                    tokens = estimate_tokens(chunk_encoded)
                    chunk_sizes.append(tokens)
                    total_tokens += tokens
                    current_chunk_items = []
            else:
                current_chunk_items.append(item)

        if current_chunk_items:
            final_encoded = self.encoder.encode(current_chunk_items)
            chunks.append(final_encoded)
            tokens = estimate_tokens(final_encoded)
            chunk_sizes.append(tokens)
            total_tokens += tokens

        return {
            'chunks': chunks,
            'metadata': {
                'total_chunks': len(chunks),
                'total_tokens': total_tokens,
                'chunk_sizes': chunk_sizes
            }
        }
