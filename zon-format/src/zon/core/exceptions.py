"""ZON exception classes for encoding and decoding errors."""

from typing import Optional


class ZonDecodeError(Exception):
    """Exception raised when ZON decoding fails.
    
    This exception provides detailed context about decoding errors including
    the error location, error code, and surrounding context.
    
    Attributes:
        code: Optional error code for programmatic error handling
        line: Line number where the error occurred
        column: Column number where the error occurred
        context: Additional context string showing the problematic input
    """
    
    def __init__(
        self, 
        message: str, 
        code: Optional[str] = None,
        line: Optional[int] = None,
        column: Optional[int] = None,
        context: Optional[str] = None
    ):
        """Initialize a ZonDecodeError with detailed context.
        
        Args:
            message: Human-readable error description
            code: Optional error code for categorizing the error
            line: Line number in the input where error occurred
            column: Column number in the input where error occurred
            context: Snippet of input text surrounding the error
        """
        super().__init__(message)
        self.code = code
        self.line = line
        self.column = column
        self.context = context
    
    def __str__(self) -> str:
        """Format the error message with all available context.
        
        Returns:
            Formatted error string including code, line number, and context
        """
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
    """Exception raised when ZON encoding fails.
    
    This exception is raised when the encoder encounters data that cannot
    be properly encoded into ZON format, such as unsupported data types or
    values that violate ZON format constraints.
    """
    pass
