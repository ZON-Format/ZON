"""
ZON Schema Validation v1.0.4 - LLM Guardrails

Provides runtime schema validation for LLM outputs.
"""

from typing import Any, Dict, List, Optional, Union, TypeVar, Generic
from dataclasses import dataclass
from .decoder import decode
from .exceptions import ZonDecodeError

T = TypeVar('T')


@dataclass
class ZonIssue:
    """A validation issue."""
    path: List[Union[str, int]]
    message: str
    code: str  # 'invalid_type', 'missing_field', 'invalid_enum', 'custom'


@dataclass
class ZonResult(Generic[T]):
    """Result of schema validation."""
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    issues: Optional[List[ZonIssue]] = None


class ZonSchema:
    """Base class for ZON schemas."""
    
    def __init__(self):
        self._description: Optional[str] = None
        self._is_optional: bool = False
    
    def describe(self, description: str) -> 'ZonSchema':
        """Add a description for prompt generation."""
        self._description = description
        return self
    
    def optional(self) -> 'ZonOptionalSchema':
        """Mark this field as optional."""
        return ZonOptionalSchema(self)
    
    def parse(self, data: Any, path: Optional[List[Union[str, int]]] = None) -> ZonResult:
        """Parse and validate data against this schema."""
        raise NotImplementedError
    
    def to_prompt(self, indent: int = 0) -> str:
        """Generate a prompt string for LLMs."""
        raise NotImplementedError


class ZonOptionalSchema(ZonSchema):
    """Wrapper for optional schemas."""
    
    def __init__(self, schema: ZonSchema):
        super().__init__()
        self._inner_schema = schema
        self._is_optional = True
    
    def parse(self, data: Any, path: Optional[List[Union[str, int]]] = None) -> ZonResult:
        if path is None:
            path = []
        
        if data is None:
            return ZonResult(success=True, data=None)
        
        return self._inner_schema.parse(data, path)
    
    def to_prompt(self, indent: int = 0) -> str:
        return f"{self._inner_schema.to_prompt(indent)} (optional)"


class ZonStringSchema(ZonSchema):
    """Schema for string values."""
    
    def parse(self, data: Any, path: Optional[List[Union[str, int]]] = None) -> ZonResult:
        if path is None:
            path = []
        
        if not isinstance(data, str):
            path_str = '.'.join(str(p) for p in path) or 'root'
            return ZonResult(
                success=False,
                error=f"Expected string at {path_str}, got {type(data).__name__}",
                issues=[ZonIssue(path=path, message=f"Expected string, got {type(data).__name__}", code='invalid_type')]
            )
        
        return ZonResult(success=True, data=data)
    
    def to_prompt(self, indent: int = 0) -> str:
        desc = f" - {self._description}" if self._description else ""
        return f"string{desc}"


class ZonNumberSchema(ZonSchema):
    """Schema for number values."""
    
    def parse(self, data: Any, path: Optional[List[Union[str, int]]] = None) -> ZonResult:
        if path is None:
            path = []
        
        if not isinstance(data, (int, float)) or isinstance(data, bool):
            path_str = '.'.join(str(p) for p in path) or 'root'
            return ZonResult(
                success=False,
                error=f"Expected number at {path_str}, got {type(data).__name__}",
                issues=[ZonIssue(path=path, message=f"Expected number, got {type(data).__name__}", code='invalid_type')]
            )
        
        # Check for NaN
        import math
        if isinstance(data, float) and math.isnan(data):
            path_str = '.'.join(str(p) for p in path) or 'root'
            return ZonResult(
                success=False,
                error=f"Expected number at {path_str}, got NaN",
                issues=[ZonIssue(path=path, message="Expected number, got NaN", code='invalid_type')]
            )
        
        return ZonResult(success=True, data=data)
    
    def to_prompt(self, indent: int = 0) -> str:
        desc = f" - {self._description}" if self._description else ""
        return f"number{desc}"


class ZonBooleanSchema(ZonSchema):
    """Schema for boolean values."""
    
    def parse(self, data: Any, path: Optional[List[Union[str, int]]] = None) -> ZonResult:
        if path is None:
            path = []
        
        if not isinstance(data, bool):
            path_str = '.'.join(str(p) for p in path) or 'root'
            return ZonResult(
                success=False,
                error=f"Expected boolean at {path_str}, got {type(data).__name__}",
                issues=[ZonIssue(path=path, message=f"Expected boolean, got {type(data).__name__}", code='invalid_type')]
            )
        
        return ZonResult(success=True, data=data)
    
    def to_prompt(self, indent: int = 0) -> str:
        desc = f" - {self._description}" if self._description else ""
        return f"boolean{desc}"


class ZonEnumSchema(ZonSchema):
    """Schema for enum values."""
    
    def __init__(self, values: List[str]):
        super().__init__()
        self._values = values
    
    def parse(self, data: Any, path: Optional[List[Union[str, int]]] = None) -> ZonResult:
        if path is None:
            path = []
        
        if data not in self._values:
            path_str = '.'.join(str(p) for p in path) or 'root'
            return ZonResult(
                success=False,
                error=f"Expected one of [{', '.join(self._values)}] at {path_str}, got '{data}'",
                issues=[ZonIssue(path=path, message=f"Invalid enum value. Expected: {', '.join(self._values)}", code='invalid_enum')]
            )
        
        return ZonResult(success=True, data=data)
    
    def to_prompt(self, indent: int = 0) -> str:
        desc = f" - {self._description}" if self._description else ""
        return f"enum({', '.join(self._values)}){desc}"


class ZonArraySchema(ZonSchema):
    """Schema for array values."""
    
    def __init__(self, element_schema: ZonSchema):
        super().__init__()
        self._element_schema = element_schema
    
    def parse(self, data: Any, path: Optional[List[Union[str, int]]] = None) -> ZonResult:
        if path is None:
            path = []
        
        if not isinstance(data, list):
            path_str = '.'.join(str(p) for p in path) or 'root'
            return ZonResult(
                success=False,
                error=f"Expected array at {path_str}, got {type(data).__name__}",
                issues=[ZonIssue(path=path, message=f"Expected array, got {type(data).__name__}", code='invalid_type')]
            )
        
        result = []
        for i, item in enumerate(data):
            item_result = self._element_schema.parse(item, path + [i])
            if not item_result.success:
                return item_result  # Return first error found
            result.append(item_result.data)
        
        return ZonResult(success=True, data=result)
    
    def to_prompt(self, indent: int = 0) -> str:
        desc = f" - {self._description}" if self._description else ""
        return f"array of [{self._element_schema.to_prompt(indent)}]{desc}"


class ZonObjectSchema(ZonSchema):
    """Schema for object values."""
    
    def __init__(self, shape: Dict[str, ZonSchema]):
        super().__init__()
        self._shape = shape
    
    def parse(self, data: Any, path: Optional[List[Union[str, int]]] = None) -> ZonResult:
        if path is None:
            path = []
        
        if not isinstance(data, dict):
            path_str = '.'.join(str(p) for p in path) or 'root'
            return ZonResult(
                success=False,
                error=f"Expected object at {path_str}, got {type(data).__name__}",
                issues=[ZonIssue(path=path, message=f"Expected object, got {type(data).__name__}", code='invalid_type')]
            )
        
        result = {}
        for key, field_schema in self._shape.items():
            # Check if field is missing (not present in data)
            if key not in data:
                # For non-optional schemas, missing fields fail validation
                if isinstance(field_schema, ZonOptionalSchema):
                    result[key] = None
                    continue
                else:
                    path_str = '.'.join(str(p) for p in (path + [key])) or 'root'
                    return ZonResult(
                        success=False,
                        error=f"Missing required field '{key}' at {path_str}",
                        issues=[ZonIssue(path=path + [key], message=f"Missing required field: {key}", code='missing_field')]
                    )
            
            field_result = field_schema.parse(data.get(key), path + [key])
            
            if not field_result.success:
                return field_result
            
            result[key] = field_result.data
        
        return ZonResult(success=True, data=result)
    
    def to_prompt(self, indent: int = 0) -> str:
        spaces = ' ' * indent
        lines = ['object:']
        if self._description:
            lines[0] += f' ({self._description})'
        
        for key, field_schema in self._shape.items():
            field_prompt = field_schema.to_prompt(indent + 2)
            lines.append(f"{spaces}  - {key}: {field_prompt}")
        
        return '\n'.join(lines)


class ZonSchemaBuilder:
    """Builder for ZON schemas."""
    
    @staticmethod
    def string() -> ZonStringSchema:
        """Create a string schema."""
        return ZonStringSchema()
    
    @staticmethod
    def number() -> ZonNumberSchema:
        """Create a number schema."""
        return ZonNumberSchema()
    
    @staticmethod
    def boolean() -> ZonBooleanSchema:
        """Create a boolean schema."""
        return ZonBooleanSchema()
    
    @staticmethod
    def enum(values: List[str]) -> ZonEnumSchema:
        """Create an enum schema."""
        return ZonEnumSchema(values)
    
    @staticmethod
    def array(element_schema: ZonSchema) -> ZonArraySchema:
        """Create an array schema."""
        return ZonArraySchema(element_schema)
    
    @staticmethod
    def object(shape: Dict[str, ZonSchema]) -> ZonObjectSchema:
        """Create an object schema."""
        return ZonObjectSchema(shape)


# Singleton builder
zon = ZonSchemaBuilder()


def validate(input_data: Any, schema: ZonSchema) -> ZonResult:
    """
    Validate a ZON string or decoded object against a schema.
    
    Args:
        input_data: ZON string or decoded object
        schema: ZON Schema
        
    Returns:
        ZonResult with success status and data/error
    """
    data = input_data
    
    if isinstance(input_data, str):
        try:
            data = decode(input_data)
        except ZonDecodeError as e:
            return ZonResult(
                success=False,
                error=f"ZON Parse Error: {str(e)}",
                issues=[ZonIssue(path=[], message=str(e), code='custom')]
            )
        except (ValueError, TypeError) as e:
            return ZonResult(
                success=False,
                error=f"ZON Parse Error: {str(e)}",
                issues=[ZonIssue(path=[], message=str(e), code='custom')]
            )
    
    return schema.parse(data)
