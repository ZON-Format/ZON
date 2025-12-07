"""Binary ZON Format (ZON-B)

MessagePack-inspired binary encoding for maximum compression.
"""

from .encoder import BinaryZonEncoder, encode_binary
from .decoder import BinaryZonDecoder, decode_binary
from .constants import MAGIC_HEADER, TypeMarker

__all__ = [
    'BinaryZonEncoder',
    'BinaryZonDecoder',
    'encode_binary',
    'decode_binary',
    'MAGIC_HEADER',
    'TypeMarker',
]
