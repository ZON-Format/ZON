"""AI SDK integration for ZON format streaming."""

from typing import AsyncGenerator, Any, AsyncIterable
from ..core.stream import ZonStreamDecoder

async def parse_zon_stream(stream: AsyncIterable[str]) -> AsyncGenerator[Any, None]:
    """Parse a stream of ZON text from an LLM into objects.
    
    Args:
        stream: Async iterable yielding ZON text chunks
        
    Yields:
        Parsed objects as they become available
    """
    decoder = ZonStreamDecoder()
    async for item in decoder.decode(stream):
        yield item
