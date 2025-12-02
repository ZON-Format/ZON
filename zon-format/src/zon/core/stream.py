"""Streaming encoder and decoder for processing ZON data incrementally."""

from typing import AsyncGenerator, Iterable, AsyncIterable, List, Optional, Any, Union
from .encoder import ZonEncoder
from .decoder import ZonDecoder
from .utils import quote_string, parse_value

class ZonStreamEncoder:
    """Streaming encoder for ZON table format.
    
    Encodes objects one at a time as table rows, suitable for processing
    large datasets without loading everything into memory.
    """
    
    def __init__(self):
        """Initialize the stream encoder."""
        self.encoder = ZonEncoder()
        self.has_written_header = False
        self.columns: Optional[List[str]] = None

    async def encode(self, source: Union[Iterable[Any], AsyncIterable[Any]]) -> AsyncGenerator[str, None]:
        """Encode a stream of objects to ZON table format.
        
        Args:
            source: Iterable or async iterable of dict objects
            
        Yields:
            ZON-encoded strings (header first, then rows)
            
        Raises:
            ValueError: If source items are not dict objects
        """
        if isinstance(source, Iterable):
            iterator = iter(source)
            async def async_gen():
                for item in iterator:
                    yield item
            async_source = async_gen()
        else:
            async_source = source

        async for item in async_source:
            if not self.has_written_header:
                if isinstance(item, dict) and item is not None:
                    self.columns = sorted(item.keys())
                    header = f"@:{','.join(self.columns)}"
                    yield header
                    self.has_written_header = True
                else:
                    raise ValueError("ZonStreamEncoder currently only supports streams of objects (tables).")

            if self.columns:
                row = []
                for col in self.columns:
                    val = item.get(col)
                    row.append(self._format_value(val))
                yield "\n" + ",".join(row)

    def _format_value(self, val: Any) -> str:
        """Format a value for ZON table output.
        
        Args:
            val: Value to format
            
        Returns:
            String representation suitable for ZON table format
        """
        if val is True: return 'T'
        if val is False: return 'F'
        if val is None: return 'null'
        if isinstance(val, (int, float)):
            return str(val)
        return quote_string(str(val))

class ZonStreamDecoder:
    """Streaming decoder for ZON table format.
    
    Decodes ZON table data incrementally, yielding objects as they are
    parsed from the stream.
    """
    
    def __init__(self):
        """Initialize the stream decoder."""
        self.decoder = ZonDecoder()
        self.buffer = ''
        self.columns: Optional[List[str]] = None
        self.is_table = False

    async def decode(self, source: Union[Iterable[str], AsyncIterable[str]]) -> AsyncGenerator[Any, None]:
        """Decode a stream of ZON table data.
        
        Args:
            source: Iterable or async iterable of string chunks
            
        Yields:
            Decoded dict objects representing table rows
        """
        if isinstance(source, Iterable):
            iterator = iter(source)
            async def async_gen():
                for item in iterator:
                    yield item
            async_source = async_gen()
        else:
            async_source = source

        async for chunk in async_source:
            self.buffer += chunk
            
            while '\n' in self.buffer:
                newline_idx = self.buffer.index('\n')
                line = self.buffer[:newline_idx].strip()
                self.buffer = self.buffer[newline_idx + 1:]

                if not line:
                    continue

                if not self.columns:
                    if line.startswith('@'):
                        self.is_table = True
                        parts = line.split(':')
                        col_part = parts[-1]
                        self.columns = col_part.split(',')
                else:
                    values = self._parse_row(line)
                    obj = {}
                    for i, col in enumerate(self.columns):
                        if i < len(values):
                            obj[col] = values[i]
                    yield obj
        
        if self.buffer.strip():
            line = self.buffer.strip()
            if self.columns:
                values = self._parse_row(line)
                obj = {}
                for i, col in enumerate(self.columns):
                    if i < len(values):
                        obj[col] = values[i]
                yield obj

    def _parse_row(self, line: str) -> List[Any]:
        """Parse a CSV-style row with ZON value syntax.
        
        Args:
            line: Row string to parse
            
        Returns:
            List of parsed values
        """
        values = []
        current = []
        in_quotes = False
        
        i = 0
        while i < len(line):
            char = line[i]
            if char == '"':
                if in_quotes and i + 1 < len(line) and line[i + 1] == '"':
                    current.append('"')
                    i += 1
                else:
                    in_quotes = not in_quotes
            elif char == ',' and not in_quotes:
                values.append(parse_value("".join(current)))
                current = []
            else:
                current.append(char)
            i += 1
        
        values.append(parse_value("".join(current)))
        return values
