"""Binary ZON Encoder

Encodes Python values to compact binary format.
"""

import struct
from typing import Any, List
from .constants import (
    MAGIC_HEADER, TypeMarker,
    create_positive_fixint, create_negative_fixint,
    create_fixmap, create_fixarray, create_fixstr
)


class BinaryZonEncoder:
    """Binary ZON Encoder"""
    
    def __init__(self):
        self.buffer: List[int] = []
    
    def encode(self, data: Any) -> bytes:
        """Encode data to binary ZON format"""
        self.buffer = []
        
        self.buffer.extend(MAGIC_HEADER)
        
        self._encode_value(data)
        
        return bytes(self.buffer)
    
    def _encode_value(self, value: Any) -> None:
        """Encode a single value"""
        if value is None:
            self.buffer.append(TypeMarker.NIL)
        elif isinstance(value, bool):
            self.buffer.append(TypeMarker.TRUE if value else TypeMarker.FALSE)
        elif isinstance(value, (int, float)):
            self._encode_number(value)
        elif isinstance(value, str):
            self._encode_string(value)
        elif isinstance(value, list):
            self._encode_array(value)
        elif isinstance(value, dict):
            self._encode_object(value)
        else:
            raise TypeError(f"Unsupported type: {type(value)}")
    
    def _encode_number(self, value: float) -> None:
        """Encode a number (int or float)"""
        if isinstance(value, bool):
            return
            
        if isinstance(value, int):
            if 0 <= value <= 127:
                self.buffer.append(create_positive_fixint(value))
            elif -32 <= value < 0:
                self.buffer.append(create_negative_fixint(value))
            elif 0 <= value <= 0xFF:
                self.buffer.append(TypeMarker.UINT8)
                self.buffer.append(value)
            elif 0 <= value <= 0xFFFF:
                self.buffer.append(TypeMarker.UINT16)
                self._write_uint16(value)
            elif 0 <= value <= 0xFFFFFFFF:
                self.buffer.append(TypeMarker.UINT32)
                self._write_uint32(value)
            elif -128 <= value <= 127:
                self.buffer.append(TypeMarker.INT8)
                self.buffer.append(value & 0xFF)
            elif -32768 <= value <= 32767:
                self.buffer.append(TypeMarker.INT16)
                self._write_int16(value)
            else:
                self.buffer.append(TypeMarker.INT32)
                self._write_int32(value)
        else:
            self.buffer.append(TypeMarker.FLOAT64)
            self._write_float64(value)
    
    def _encode_string(self, value: str) -> None:
        """Encode a string"""
        encoded = value.encode('utf-8')
        length = len(encoded)
        
        if length <= 31:
            self.buffer.append(create_fixstr(length))
        elif length <= 0xFF:
            self.buffer.append(TypeMarker.STR8)
            self.buffer.append(length)
        elif length <= 0xFFFF:
            self.buffer.append(TypeMarker.STR16)
            self._write_uint16(length)
        else:
            self.buffer.append(TypeMarker.STR32)
            self._write_uint32(length)
        
        self.buffer.extend(encoded)
    
    def _encode_array(self, value: List[Any]) -> None:
        """Encode an array"""
        length = len(value)
        
        if length <= 15:
            self.buffer.append(create_fixarray(length))
        elif length <= 0xFFFF:
            self.buffer.append(TypeMarker.ARRAY16)
            self._write_uint16(length)
        else:
            self.buffer.append(TypeMarker.ARRAY32)
            self._write_uint32(length)
        
        for item in value:
            self._encode_value(item)
    
    def _encode_object(self, value: dict) -> None:
        """Encode an object/map"""
        length = len(value)
        
        if length <= 15:
            self.buffer.append(create_fixmap(length))
        elif length <= 0xFFFF:
            self.buffer.append(TypeMarker.MAP16)
            self._write_uint16(length)
        else:
            self.buffer.append(TypeMarker.MAP32)
            self._write_uint32(length)
        
        for key, val in value.items():
            if not isinstance(key, str):
                key = str(key)
            self._encode_string(key)
            self._encode_value(val)
    
    def _write_uint16(self, value: int) -> None:
        """Write unsigned 16-bit integer (big-endian)"""
        self.buffer.extend(struct.pack('>H', value))
    
    def _write_uint32(self, value: int) -> None:
        """Write unsigned 32-bit integer (big-endian)"""
        self.buffer.extend(struct.pack('>I', value))
    
    def _write_int16(self, value: int) -> None:
        """Write signed 16-bit integer (big-endian)"""
        self.buffer.extend(struct.pack('>h', value))
    
    def _write_int32(self, value: int) -> None:
        """Write signed 32-bit integer (big-endian)"""
        self.buffer.extend(struct.pack('>i', value))
    
    def _write_float64(self, value: float) -> None:
        """Write 64-bit float (big-endian)"""
        self.buffer.extend(struct.pack('>d', value))


def encode_binary(data: Any) -> bytes:
    """Encode data to binary ZON format
    
    Args:
        data: Python data structure to encode
        
    Returns:
        Binary ZON encoded bytes
        
    Example:
        >>> data = {"name": "Alice", "age": 30}
        >>> binary = encode_binary(data)
        >>> len(binary) < len(json.dumps(data))  # Smaller than JSON
        True
    """
    encoder = BinaryZonEncoder()
    return encoder.encode(data)
