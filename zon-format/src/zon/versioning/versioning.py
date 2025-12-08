"""ZON Document Versioning Utilities

Provides version embedding, extraction, comparison, and validation
for ZON documents to support schema evolution and backward compatibility.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import time


@dataclass
class ZonDocumentMetadata:
    """Metadata for versioned ZON documents"""
    
    version: str
    """Semantic version of the document format (e.g., "1.3.0")"""
    
    schema_id: Optional[str] = None
    """Optional schema identifier (e.g., "user-profile-v2")"""
    
    encoding: str = 'zon'
    """Encoding format used ("zon" | "zon-binary")"""
    
    timestamp: Optional[int] = None
    """Unix timestamp when document was created"""
    
    custom: Dict[str, Any] = field(default_factory=dict)
    """Custom metadata fields"""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            'version': self.version,
            'encoding': self.encoding
        }
        if self.schema_id:
            result['schemaId'] = self.schema_id
        if self.timestamp:
            result['timestamp'] = self.timestamp
        if self.custom:
            result['custom'] = self.custom
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ZonDocumentMetadata':
        """Create from dictionary"""
        return cls(
            version=data['version'],
            schema_id=data.get('schemaId'),
            encoding=data.get('encoding', 'zon'),
            timestamp=data.get('timestamp'),
            custom=data.get('custom', {})
        )


def embed_version(
    data: Any,
    version: str,
    schema_id: Optional[str] = None,
    encoding: str = 'zon'
) -> Dict[str, Any]:
    """Embeds version metadata into a data object.
    
    Adds a special __zon_meta field to the root object.
    
    Args:
        data: Data object to add metadata to
        version: Semantic version string (e.g., "1.0.0")
        schema_id: Optional schema identifier
        encoding: Encoding format ('zon' or 'zon-binary')
        
    Returns:
        Data object with embedded metadata
        
    Raises:
        TypeError: If data is not a dict
        
    Example:
        >>> data = {"users": [{"id": 1, "name": "Alice"}]}
        >>> versioned = embed_version(data, "2.0.0", "user-schema")
        >>> versioned['__zon_meta']['version']
        '2.0.0'
    """
    if not isinstance(data, dict):
        raise TypeError('Can only embed version in root objects')
    
    metadata = ZonDocumentMetadata(
        version=version,
        schema_id=schema_id,
        encoding=encoding,
        timestamp=int(time.time_ns() // 1_000_000)  # milliseconds
    )
    
    return {
        '__zon_meta': metadata.to_dict(),
        **data
    }


def extract_version(data: Any) -> Optional[ZonDocumentMetadata]:
    """Extracts version metadata from a decoded ZON document.
    
    Args:
        data: Decoded data object
        
    Returns:
        Metadata if present, None otherwise
        
    Example:
        >>> decoded = decode(zon_string)
        >>> meta = extract_version(decoded)
        >>> if meta:
        ...     print(f"Version: {meta.version}")
    """
    if not isinstance(data, dict) or '__zon_meta' not in data:
        return None
    
    meta = data['__zon_meta']
    
    if not isinstance(meta, dict) or 'version' not in meta:
        return None
    
    return ZonDocumentMetadata.from_dict(meta)


def strip_version(data: Any) -> Any:
    """Removes version metadata from a data object.
    
    Args:
        data: Data object with metadata
        
    Returns:
        Data object without __zon_meta field
        
    Example:
        >>> versioned = {"__zon_meta": {...}, "users": [...]}
        >>> clean = strip_version(versioned)
        >>> '__zon_meta' in clean
        False
    """
    if not isinstance(data, dict):
        return data
    
    return {k: v for k, v in data.items() if k != '__zon_meta'}


def compare_versions(v1: str, v2: str) -> int:
    """Compare two semantic version strings.
    
    Args:
        v1: First version string (e.g., "1.2.3")
        v2: Second version string (e.g., "1.3.0")
        
    Returns:
        -1 if v1 < v2, 0 if v1 == v2, 1 if v1 > v2
        
    Example:
        >>> compare_versions("1.2.0", "1.3.0")
        -1
        >>> compare_versions("2.0.0", "1.9.9")
        1
    """
    def parse_version(v: str) -> tuple:
        try:
            parts = v.split('.')
            return tuple(int(p) for p in parts[:3])
        except (ValueError, AttributeError):
            return (0, 0, 0)
    
    v1_tuple = parse_version(v1)
    v2_tuple = parse_version(v2)
    
    if v1_tuple < v2_tuple:
        return -1
    elif v1_tuple > v2_tuple:
        return 1
    else:
        return 0


def is_compatible(current_version: str, required_version: str) -> bool:
    """Check if current version is compatible with required version.
    
    Compatible means current >= required for the same major version.
    
    Args:
        current_version: Current version string
        required_version: Required minimum version string
        
    Returns:
        True if compatible, False otherwise
        
    Example:
        >>> is_compatible("1.3.0", "1.2.0")
        True
        >>> is_compatible("2.0.0", "1.9.0")
        False
    """
    def parse_version(v: str) -> tuple:
        try:
            parts = v.split('.')
            return tuple(int(p) for p in parts[:3])
        except (ValueError, AttributeError):
            return (0, 0, 0)
    
    current = parse_version(current_version)
    required = parse_version(required_version)
    
    if current[0] != required[0]:
        return False
    
    return current >= required
