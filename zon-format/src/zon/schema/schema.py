"""ZON Schema Validation - Runtime schema validation for LLM outputs.

Provides a Zod-like schema builder and validator for ensuring LLM outputs
match expected structures and constraints.
"""

from typing import Any, Dict, List, Optional, Union, TypeVar, Generic
from dataclasses import dataclass
from ..core.decoder import decode
from ..core.exceptions import ZonDecodeError

T = TypeVar('T')


@dataclass
class ZonIssue:
    """A validation issue."""
    path: List[Union[str, int]]
    message: str
    code: str


@dataclass
class ZonResult(Generic[T]):
    """Result of schema validation."""
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    issues: Optional[List[ZonIssue]] = None


import re
from datetime import datetime, date, time

class ZonSchema:
    """Base class for all ZON schemas.
    
    Provides common functionality for schema definition, validation,
    and prompt generation.
    """
    
    def __init__(self):
        self._description: Optional[str] = None
        self._is_optional: bool = False
        self._default_value: Any = None
        self._has_default: bool = False
        self._refinements: List[Tuple[callable, str]] = []
        self._example_value: Any = None
    
    def example(self, value: Any) -> 'ZonSchema':
        """Set an example value for the schema.
        
        Args:
            value: Example value
            
        Returns:
            Self for chaining
        """
        self._example_value = value
        return self
    
    def describe(self, description: str) -> 'ZonSchema':
        """Add a natural language description for prompt generation.
        
        Args:
            description: Description string
            
        Returns:
            Self for chaining
        """
        self._description = description
        return self
    
    def optional(self) -> 'ZonOptionalSchema':
        """Mark this field as optional."""
        return ZonOptionalSchema(self)

    def nullable(self) -> 'ZonNullableSchema':
        """Mark this field as nullable."""
        return ZonNullableSchema(self)
    
    def default(self, value: Any) -> 'ZonSchema':
        """Set a default value to use if field is missing or None.
        
        Args:
            value: Default value
            
        Returns:
            Self for chaining
        """
        self._default_value = value
        self._has_default = True
        return self

    def refine(self, validator: callable, message: str) -> 'ZonSchema':
        """Add a custom validation rule.
        
        Args:
            validator: Callable taking the value and returning bool
            message: Error message if validation fails
            
        Returns:
            Self for chaining
        """
        self._refinements.append((validator, message))
        return self
    
    def parse(self, data: Any, path: Optional[List[Union[str, int]]] = None) -> ZonResult:
        """Parse and validate data against this schema.
        
        Args:
            data: Data to validate
            path: Current path in the data structure
            
        Returns:
            Validation result
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError
    
    def _apply_refinements(self, data: Any, path: List[Union[str, int]]) -> Optional[ZonResult]:
        for validator, message in self._refinements:
            if not validator(data):
                path_str = '.'.join(str(p) for p in path) or 'root'
                return ZonResult(
                    success=False,
                    error=message,
                    issues=[ZonIssue(path=path, message=message, code='custom_refinement')]
                )
        return None

    def to_prompt(self, indent: int = 0) -> str:
        """Generate a prompt string describing the schema for LLMs.
        
        Args:
            indent: Indentation level
            
        Returns:
            Schema description string
        """
        raise NotImplementedError
    
    def toPrompt(self) -> str:
        """Alias for to_prompt to match TS API in tests."""
        return self.to_prompt()


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


class ZonNullableSchema(ZonSchema):
    """Wrapper for nullable schemas."""
    
    def __init__(self, schema: ZonSchema):
        super().__init__()
        self._inner_schema = schema
    
    def parse(self, data: Any, path: Optional[List[Union[str, int]]] = None) -> ZonResult:
        if path is None:
            path = []
        
        if data is None:
            return ZonResult(success=True, data=None)
        
        return self._inner_schema.parse(data, path)
    
    def to_prompt(self, indent: int = 0) -> str:
        return f"{self._inner_schema.to_prompt(indent)} (nullable)"


class ZonStringSchema(ZonSchema):
    """Schema for string values with validation constraints."""
    
    def __init__(self):
        super().__init__()
        self._min_len: Optional[int] = None
        self._max_len: Optional[int] = None
        self._is_email: bool = False
        self._is_url: bool = False
        self._nullable: bool = False
        self._regex: Optional[Tuple[str, str]] = None
        self._is_uuid: Optional[str] = None
        self._is_datetime: bool = False
        self._is_date: bool = False
        self._is_time: bool = False

    def min(self, length: int) -> 'ZonStringSchema':
        self._min_len = length
        return self

    def max(self, length: int) -> 'ZonStringSchema':
        self._max_len = length
        return self

    def email(self) -> 'ZonStringSchema':
        self._is_email = True
        return self

    def url(self) -> 'ZonStringSchema':
        self._is_url = True
        return self
    
    def nullable(self) -> 'ZonNullableSchema':
        return ZonNullableSchema(self)

    def regex(self, pattern: str, message: str = "Pattern mismatch") -> 'ZonStringSchema':
        self._regex = (pattern, message)
        return self

    def uuid(self, version: Optional[str] = None) -> 'ZonStringSchema':
        self._is_uuid = version or 'any'
        return self

    def datetime(self) -> 'ZonStringSchema':
        self._is_datetime = True
        return self

    def date(self) -> 'ZonStringSchema':
        self._is_date = True
        return self

    def time(self) -> 'ZonStringSchema':
        self._is_time = True
        return self
    
    def parse(self, data: Any, path: Optional[List[Union[str, int]]] = None) -> ZonResult:
        if path is None:
            path = []
        
        if data is None:
            if self._has_default:
                return ZonResult(success=True, data=self._default_value)
            if self._nullable:
                return ZonResult(success=True, data=None)
            else:
                path_str = '.'.join(str(p) for p in path) or 'root'
                return ZonResult(
                    success=False,
                    error=f"Expected string at {path_str}, got None",
                    issues=[ZonIssue(path=path, message="Expected string, got None", code='invalid_type')]
                )

        if not isinstance(data, str):
            path_str = '.'.join(str(p) for p in path) or 'root'
            return ZonResult(
                success=False,
                error=f"Expected string at {path_str}, got {type(data).__name__}",
                issues=[ZonIssue(path=path, message=f"Expected string, got {type(data).__name__}", code='invalid_type')]
            )
        
        if self._min_len is not None and len(data) < self._min_len:
            return ZonResult(
                success=False,
                error=f"String too short",
                issues=[ZonIssue(path=path, message=f"String too short (min {self._min_len})", code='too_short')]
            )

        if self._max_len is not None and len(data) > self._max_len:
            return ZonResult(
                success=False,
                error=f"String too long",
                issues=[ZonIssue(path=path, message=f"String too long (max {self._max_len})", code='too_long')]
            )

        if self._is_email:
            if '@' not in data:
                 return ZonResult(
                    success=False,
                    error=f"Invalid email",
                    issues=[ZonIssue(path=path, message="Invalid email", code='invalid_format')]
                )

        if self._is_url:
            if not data.startswith(('http://', 'https://')):
                 return ZonResult(
                    success=False,
                    error=f"Invalid URL",
                    issues=[ZonIssue(path=path, message="Invalid URL", code='invalid_format')]
                )

        if self._regex:
            pattern, msg = self._regex
            if not re.search(pattern, data):
                return ZonResult(
                    success=False,
                    error=msg,
                    issues=[ZonIssue(path=path, message=msg, code='invalid_format')]
                )

        if self._is_uuid:
            uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
            if not re.match(uuid_pattern, data.lower()):
                 return ZonResult(
                    success=False,
                    error="Invalid UUID",
                    issues=[ZonIssue(path=path, message="Invalid UUID", code='invalid_format')]
                )
            if self._is_uuid == 'v4':
                if data[14] != '4':
                     return ZonResult(
                        success=False,
                        error="Invalid UUID v4",
                        issues=[ZonIssue(path=path, message="Invalid UUID v4", code='invalid_format')]
                    )

        if self._is_datetime:
            try:
                d = data.replace('Z', '+00:00')
                dt = datetime.fromisoformat(d)
                if 'T' not in data and ' ' not in data:
                     raise ValueError("Missing time component")
            except ValueError:
                 return ZonResult(
                    success=False,
                    error="Invalid datetime",
                    issues=[ZonIssue(path=path, message="Invalid datetime", code='invalid_format')]
                )

        if self._is_date:
            try:
                date.fromisoformat(data)
                if 'T' in data: raise ValueError
            except ValueError:
                 return ZonResult(
                    success=False,
                    error="Invalid date",
                    issues=[ZonIssue(path=path, message="Invalid date", code='invalid_format')]
                )

        if self._is_time:
            if not re.match(r'^\d{2}:\d{2}:\d{2}$', data):
                 return ZonResult(
                    success=False,
                    error="Invalid time",
                    issues=[ZonIssue(path=path, message="Invalid time", code='invalid_format')]
                )

        refinement_error = self._apply_refinements(data, path)
        if refinement_error:
            return refinement_error

        return ZonResult(success=True, data=data)
    
    def to_prompt(self, indent: int = 0) -> str:
        parts = ["string"]
        if self._description:
            parts.append(f"- {self._description}")
        if self._has_default:
            parts.append(f'(default: "{self._default_value}")')
        if self._regex:
            parts.append(f'(pattern: "{self._regex[0]}")')
        if self._is_uuid:
            parts.append(f'(uuid-{self._is_uuid})')
        if self._is_datetime:
            parts.append('(datetime)')
        
        return " ".join(parts)


class ZonNumberSchema(ZonSchema):
    """Schema for number values with constraints."""
    
    def __init__(self):
        super().__init__()
        self._min_val: Optional[Union[int, float]] = None
        self._max_val: Optional[Union[int, float]] = None
        self._is_int: bool = False
        self._is_int: bool = False
        self._is_positive: bool = False
        self._is_negative: bool = False

    def min(self, val: Union[int, float]) -> 'ZonNumberSchema':
        self._min_val = val
        return self

    def max(self, val: Union[int, float]) -> 'ZonNumberSchema':
        self._max_val = val
        return self

    def int(self) -> 'ZonNumberSchema':
        self._is_int = True
        return self

    def positive(self) -> 'ZonNumberSchema':
        self._is_positive = True
        return self

    def negative(self) -> 'ZonNumberSchema':
        self._is_negative = True
        return self
    
    def parse(self, data: Any, path: Optional[List[Union[str, int]]] = None) -> ZonResult:
        if path is None:
            path = []
        
        if data is None:
            if self._has_default:
                return ZonResult(success=True, data=self._default_value)
        
        if not isinstance(data, (int, float)) or isinstance(data, bool):
            path_str = '.'.join(str(p) for p in path) or 'root'
            return ZonResult(
                success=False,
                error=f"Expected number at {path_str}, got {type(data).__name__}",
                issues=[ZonIssue(path=path, message=f"Expected number, got {type(data).__name__}", code='invalid_type')]
            )
        
        import math
        if isinstance(data, float) and math.isnan(data):
            path_str = '.'.join(str(p) for p in path) or 'root'
            return ZonResult(
                success=False,
                error=f"Expected number at {path_str}, got NaN",
                issues=[ZonIssue(path=path, message="Expected number, got NaN", code='invalid_type')]
            )

        if self._is_int and not isinstance(data, int):
             if isinstance(data, float) and data.is_integer():
                 pass
             else:
                return ZonResult(
                    success=False,
                    error=f"Expected integer",
                    issues=[ZonIssue(path=path, message="Expected integer", code='invalid_type')]
                )

        if self._is_positive and data <= 0:
            return ZonResult(
                success=False,
                error=f"Expected positive number",
                issues=[ZonIssue(path=path, message="Expected positive number", code='invalid_value')]
            )

        if self._is_negative and data >= 0:
            return ZonResult(
                success=False,
                error=f"Expected negative number",
                issues=[ZonIssue(path=path, message="Expected negative number", code='invalid_value')]
            )

        if self._min_val is not None and data < self._min_val:
            return ZonResult(
                success=False,
                error=f"Number too small",
                issues=[ZonIssue(path=path, message=f"Number too small (min {self._min_val})", code='too_small')]
            )

        if self._max_val is not None and data > self._max_val:
            return ZonResult(
                success=False,
                error=f"Number too large",
                issues=[ZonIssue(path=path, message=f"Number too large (max {self._max_val})", code='too_large')]
            )
        
        refinement_error = self._apply_refinements(data, path)
        if refinement_error:
            return refinement_error
            
        return ZonResult(success=True, data=data)
    
    def to_prompt(self, indent: int = 0) -> str:
        desc = f" - {self._description}" if self._description else ""
        constraints = []
        if self._is_int: constraints.append("integer")
        if self._is_positive: constraints.append("positive")
        if self._is_negative: constraints.append("negative")
        if self._min_val is not None: constraints.append(f"min: {self._min_val}")
        if self._max_val is not None: constraints.append(f"max: {self._max_val}")
        
        constraint_str = f" ({', '.join(constraints)})" if constraints else ""
        return f"number{constraint_str}{desc}"


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


class ZonLiteralSchema(ZonSchema):
    """Schema for literal values."""
    
    def __init__(self, value: Any):
        super().__init__()
        self._value = value
    
    def parse(self, data: Any, path: Optional[List[Union[str, int]]] = None) -> ZonResult:
        if path is None:
            path = []
        
        if data != self._value:
            path_str = '.'.join(str(p) for p in path) or 'root'
            return ZonResult(
                success=False,
                error=f"Expected literal '{self._value}' at {path_str}, got '{data}'",
                issues=[ZonIssue(path=path, message=f"Expected literal '{self._value}'", code='invalid_literal')]
            )
        
        return ZonResult(success=True, data=data)
    
    def to_prompt(self, indent: int = 0) -> str:
        val_str = f'"{self._value}"' if isinstance(self._value, str) else str(self._value)
        return f"{val_str}"


class ZonUnionSchema(ZonSchema):
    """Schema for union types."""
    
    def __init__(self, schemas: List[ZonSchema]):
        super().__init__()
        self._schemas = schemas
    
    def parse(self, data: Any, path: Optional[List[Union[str, int]]] = None) -> ZonResult:
        if path is None:
            path = []
        
        errors = []
        for schema in self._schemas:
            result = schema.parse(data, path)
            if result.success:
                refinement_error = self._apply_refinements(data, path)
                if refinement_error:
                    return refinement_error
                return result
            errors.append(result.error)
        
        path_str = '.'.join(str(p) for p in path) or 'root'
        return ZonResult(
            success=False,
            error=f"Invalid union value at {path_str}",
            issues=[ZonIssue(path=path, message=f"Invalid union value", code='invalid_union')]
        )
    
    def to_prompt(self, indent: int = 0) -> str:
        options = [s.to_prompt(indent) for s in self._schemas]
        return f"oneOf({ ' | '.join(options) })"


class ZonArraySchema(ZonSchema):
    """Schema for array values."""
    
    def __init__(self, element_schema: ZonSchema):
        super().__init__()
        self._element_schema = element_schema
        self._min_len: Optional[int] = None
        self._max_len: Optional[int] = None

    def min(self, length: int) -> 'ZonArraySchema':
        self._min_len = length
        return self

    def max(self, length: int) -> 'ZonArraySchema':
        self._max_len = length
        return self
    
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

        if self._min_len is not None and len(data) < self._min_len:
            return ZonResult(
                success=False,
                error=f"Array too short",
                issues=[ZonIssue(path=path, message=f"Array too short (min {self._min_len})", code='too_short')]
            )

        if self._max_len is not None and len(data) > self._max_len:
            return ZonResult(
                success=False,
                error=f"Array too long",
                issues=[ZonIssue(path=path, message=f"Array too long (max {self._max_len})", code='too_long')]
            )
        
        result = []
        for i, item in enumerate(data):
            item_result = self._element_schema.parse(item, path + [i])
            if not item_result.success:
                return item_result
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
        
        if data is None and self._has_default:
            data = self._default_value
            
        if not isinstance(data, dict):
            path_str = '.'.join(str(p) for p in path) or 'root'
            return ZonResult(
                success=False,
                error=f"Expected object at {path_str}, got {type(data).__name__}",
                issues=[ZonIssue(path=path, message=f"Expected object, got {type(data).__name__}", code='invalid_type')]
            )
        
        result = {}
        for key, field_schema in self._shape.items():
            if key not in data:
                if field_schema._has_default:
                    result[key] = field_schema._default_value
                    continue

                if isinstance(field_schema, ZonOptionalSchema):
                    result[key] = None
                    continue
                
                if field_schema._is_optional:
                     result[key] = None
                     continue

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
        
        refinement_error = self._apply_refinements(result, path)
        if refinement_error:
            return refinement_error

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
    """Builder factory for creating ZON schemas.
    
    Provides static methods to create various schema types (string, number,
    object, array, etc.) similar to Zod.
    """
    
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

    @staticmethod
    def literal(value: Any) -> ZonLiteralSchema:
        """Create a literal schema."""
        return ZonLiteralSchema(value)

    @staticmethod
    def union(*schemas: ZonSchema) -> ZonUnionSchema:
        """Create a union schema."""
        return ZonUnionSchema(list(schemas))


zon = ZonSchemaBuilder()


def validate(input_data: Any, schema: ZonSchema) -> ZonResult:
    """Validate a ZON string or decoded object against a schema.
    
    Args:
        input_data: ZON string or decoded object (dict/list)
        schema: ZON Schema definition
        
    Returns:
        ZonResult object containing success status and validated data or errors
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
