"""Binary ZON Decoder

Decodes binary ZON format back to Python values.
"""

import struct
from typing import Any
from .constants import (
    MAGIC_HEADER, TypeMarker,
    is_positive_fixint, is_negative_fixint,
    is_fixmap, get_fixmap_size,
    is_fixarray, get_fixarray_size,
    is_fixstr, get_fixstr_size
)


class BinaryZonDecoder:
    """Binary ZON Decoder"""
    
    def __init__(self):
        self.data: bytes = b''
        self.pos: int = 0
    
    def decode(self, data: bytes) -> Any:
        """Decode binary ZON format to Python value"""
        self.data = data
        self.pos = 0
        
        if len(data) < 4 or data[:4] != MAGIC_HEADER:
            raise ValueError("Invalid binary ZON format: missing or invalid magic header")
        
        self.pos = 4
        
        return self._decode_value()
    
    def _decode_value(self) -> Any:
        """Decode a single value"""
        if self.pos >= len(self.data):
            raise ValueError("Unexpected end of data")
        
        byte = self.data[self.pos]
        self.pos += 1
        
        if byte == TypeMarker.NIL:
            return None
        elif byte == TypeMarker.FALSE:
            return False
        elif byte == TypeMarker.TRUE:
            return True
        elif is_positive_fixint(byte):
            return byte
        elif is_negative_fixint(byte):
            return struct.unpack('b', bytes([byte]))[0]
        elif is_fixstr(byte):
            length = get_fixstr_size(byte)
            return self._read_string(length)
        elif is_fixarray(byte):
            length = get_fixarray_size(byte)
            return self._read_array(length)
        elif is_fixmap(byte):
            length = get_fixmap_size(byte)
            return self._read_map(length)
        elif byte == TypeMarker.UINT8:
            return self._read_uint8()
        elif byte == TypeMarker.UINT16:
            return self._read_uint16()
        elif byte == TypeMarker.UINT32:
            return self._read_uint32()
        elif byte == TypeMarker.INT8:
            return self._read_int8()
        elif byte == TypeMarker.INT16:
            return self._read_int16()
        elif byte == TypeMarker.INT32:
            return self._read_int32()
        elif byte == TypeMarker.FLOAT64:
            return self._read_float64()
        elif byte == TypeMarker.STR8:
            length = self._read_uint8()
            return self._read_string(length)
        elif byte == TypeMarker.STR16:
            length = self._read_uint16()
            return self._read_string(length)
        elif byte == TypeMarker.STR32:
            length = self._read_uint32()
            return self._read_string(length)
        elif byte == TypeMarker.ARRAY16:
            length = self._read_uint16()
            return self._read_array(length)
        elif byte == TypeMarker.ARRAY32:
            length = self._read_uint32()
            return self._read_array(length)
        elif byte == TypeMarker.MAP16:
            length = self._read_uint16()
            return self._read_map(length)
        elif byte == TypeMarker.MAP32:
            length = self._read_uint32()
            return self._read_map(length)
        else:
            raise ValueError(f"Unknown type marker: 0x{byte:02X}")
    
    def _read_uint8(self) -> int:
        """Read unsigned 8-bit integer"""
        value = self.data[self.pos]
        self.pos += 1
        return value
    
    def _read_uint16(self) -> int:
        """Read unsigned 16-bit integer (big-endian)"""
        value = struct.unpack('>H', self.data[self.pos:self.pos+2])[0]
        self.pos += 2
        return value
    
    def _read_uint32(self) -> int:
        """Read unsigned 32-bit integer (big-endian)"""
        value = struct.unpack('>I', self.data[self.pos:self.pos+4])[0]
        self.pos += 4
        return value
    
    def _read_int8(self) -> int:
        """Read signed 8-bit integer"""
        value = struct.unpack('b', self.data[self.pos:self.pos+1])[0]
        self.pos += 1
        return value
    
    def _read_int16(self) -> int:
        """Read signed 16-bit integer (big-endian)"""
        value = struct.unpack('>h', self.data[self.pos:self.pos+2])[0]
        self.pos += 2
        return value
    
    def _read_int32(self) -> int:
        """Read signed 32-bit integer (big-endian)"""
        value = struct.unpack('>i', self.data[self.pos:self.pos+4])[0]
        self.pos += 4
        return value
    
    def _read_float64(self) -> float:
        """Read 64-bit float (big-endian)"""
        value = struct.unpack('>d', self.data[self.pos:self.pos+8])[0]
        self.pos += 8
        return value
    
    def _read_string(self, length: int) -> str:
        """Read string of given length"""
        value = self.data[self.pos:self.pos+length].decode('utf-8')
        self.pos += length
        return value
    
    def _read_array(self, length: int) -> list:
        """Read array of given length"""
        return [self._decode_value() for _ in range(length)]
    
    def _read_map(self, length: int) -> dict:
        """Read map/object of given length"""
        result = {}
        for _ in range(length):
            key = self._decode_value()
            value = self._decode_value()
            result[key] = value
        return result


def decode_binary(data: bytes) -> Any:
    """Decode binary ZON format to Python value
    
    Args:
        data: Binary ZON encoded bytes
        
    Returns:
        Decoded Python data structure
        
    Example:
        >>> binary = encode_binary({"name": "Alice"})
        >>> decode_binary(binary)
        {'name': 'Alice'}
    """
    decoder = BinaryZonDecoder()
    return decoder.decode(data)
