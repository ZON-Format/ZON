"""ZON Exceptions"""

from typing import Optional


class ZonDecodeError(Exception):
    """Exception for ZON decoding errors with detailed context."""
    
    def __init__(
        self, 
        message: str, 
        code: Optional[str] = None,
        line: Optional[int] = None,
        column: Optional[int] = None,
        context: Optional[str] = None
    ):
        super().__init__(message)
        self.code = code
        self.line = line
        self.column = column
        self.context = context
    
    def __str__(self) -> str:
        msg = f"ZonDecodeError"
        if self.code:
            msg += f" [{self.code}]"
        msg += f": {self.args[0]}"
        if self.line is not None:
            msg += f" (line {self.line})"
        if self.context:
            msg += f"\n  Context: {self.context}"
        return msg


class ZonEncodeError(Exception):
    """Exception for ZON encoding errors."""
    pass
