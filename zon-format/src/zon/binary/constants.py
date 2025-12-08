"""Binary ZON Format Constants and Type Markers

Inspired by MessagePack with ZON-specific extensions.
"""

MAGIC_HEADER = bytes([0x5A, 0x4E, 0x42, 0x01])


class TypeMarker:
    """Type markers for Binary ZON"""
    
    NIL = 0xC0
    FALSE = 0xC2
    TRUE = 0xC3
    
    BIN8 = 0xC4
    BIN16 = 0xC5
    BIN32 = 0xC6
    
    STR8 = 0xD9
    STR16 = 0xDA
    STR32 = 0xDB
    
    ARRAY16 = 0xDC
    ARRAY32 = 0xDD
    
    MAP16 = 0xDE
    MAP32 = 0xDF
    
    FLOAT32 = 0xCA
    FLOAT64 = 0xCB
    
    UINT8 = 0xCC
    UINT16 = 0xCD
    UINT32 = 0xCE
    UINT64 = 0xCF
    
    INT8 = 0xD0
    INT16 = 0xD1
    INT32 = 0xD2
    INT64 = 0xD3
    
    EXT_METADATA = 0xD4
    EXT_COMPRESSED = 0xD5
    EXT_TABLE = 0xD6
    EXT_DELTA = 0xD7
    EXT_SPARSE = 0xD8


def is_positive_fixint(byte: int) -> bool:
    """Check if byte is a positive fixint (0x00-0x7F)"""
    return 0x00 <= byte <= 0x7F


def is_negative_fixint(byte: int) -> bool:
    """Check if byte is a negative fixint (0xE0-0xFF)"""
    return 0xE0 <= byte <= 0xFF


def is_fixmap(byte: int) -> bool:
    """Check if byte is a fixmap marker (0x80-0x8F)"""
    return 0x80 <= byte <= 0x8F


def get_fixmap_size(byte: int) -> int:
    """Get fixmap size from marker"""
    return byte & 0x0F


def is_fixarray(byte: int) -> bool:
    """Check if byte is a fixarray marker (0x90-0x9F)"""
    return 0x90 <= byte <= 0x9F


def get_fixarray_size(byte: int) -> int:
    """Get fixarray size from marker"""
    return byte & 0x0F


def is_fixstr(byte: int) -> bool:
    """Check if byte is a fixstr marker (0xA0-0xBF)"""
    return 0xA0 <= byte <= 0xBF


def get_fixstr_size(byte: int) -> int:
    """Get fixstr size from marker"""
    return byte & 0x1F


def create_positive_fixint(value: int) -> int:
    """Create fixint marker for positive integers 0-127"""
    return value & 0x7F


def create_negative_fixint(value: int) -> int:
    """Create negative fixint marker for integers -32 to -1"""
    return value & 0xFF


def create_fixmap(size: int) -> int:
    """Create fixmap marker for maps with 0-15 entries"""
    return 0x80 | (size & 0x0F)


def create_fixarray(size: int) -> int:
    """Create fixarray marker for arrays with 0-15 elements"""
    return 0x90 | (size & 0x0F)


def create_fixstr(size: int) -> int:
    """Create fixstr marker for strings with 0-31 bytes"""
    return 0xA0 | (size & 0x1F)
