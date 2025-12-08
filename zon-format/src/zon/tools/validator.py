"""Enhanced Validator & Linter

Validate ZON data and provide best practice recommendations.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from ..core.decoder import decode, ZonDecodeError
from .helpers import analyze


@dataclass
class ValidationError:
    """Validation error"""
    path: str
    message: str
    severity: str = 'error'


@dataclass
class ValidationWarning:
    """Validation warning"""
    path: str
    message: str
    rule: str
    severity: str = 'warning'


@dataclass
class ValidationResult:
    """Result of validation"""
    valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationWarning] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class LintOptions:
    """Options for linting"""
    max_depth: Optional[int] = None
    max_fields: Optional[int] = None
    check_irregularity: bool = True
    check_performance: bool = True


class ZonValidator:
    """Enhanced validator with linting"""
    
    def validate(
        self,
        zon_string: str,
        options: Optional[LintOptions] = None
    ) -> ValidationResult:
        """Validate ZON string and provide detailed feedback.
        
        Args:
            zon_string: ZON-encoded string to validate
            options: Validation options
            
        Returns:
            ValidationResult with errors, warnings, and suggestions
            
        Example:
            >>> validator = ZonValidator()
            >>> result = validator.validate("name:Alice\\nage:30")
            >>> result.valid
            True
        """
        if options is None:
            options = LintOptions()
        
        errors = []
        warnings = []
        suggestions = []
        
        # Try to decode
        try:
            data = decode(zon_string)
        except ZonDecodeError as e:
            return ValidationResult(
                valid=False,
                errors=[ValidationError('root', str(e), 'error')],
                warnings=[],
                suggestions=['Check ZON syntax for errors']
            )
        except Exception as e:
            return ValidationResult(
                valid=False,
                errors=[ValidationError('root', f'Unexpected error: {str(e)}', 'error')],
                warnings=[],
                suggestions=['Check data format']
            )
        
        # Analyze structure
        try:
            stats = analyze(data)
            
            # Check depth
            if options.max_depth and stats['depth'] > options.max_depth:
                warnings.append(ValidationWarning(
                    'root',
                    f"Nesting depth ({stats['depth']}) exceeds maximum ({options.max_depth})",
                    'max-depth',
                    'warning'
                ))
                suggestions.append('Consider flattening nested structures')
            
            # Check field count
            if options.max_fields and stats['field_count'] > options.max_fields:
                warnings.append(ValidationWarning(
                    'root',
                    f"Field count ({stats['field_count']}) exceeds maximum ({options.max_fields})",
                    'max-fields',
                    'warning'
                ))
                suggestions.append('Consider splitting into multiple documents')
            
            # Performance checks
            if options.check_performance:
                if stats['depth'] > 5:
                    suggestions.append('Deep nesting may impact performance')
                
                if stats['field_count'] > 100:
                    suggestions.append('Large number of fields may impact serialization speed')
        
        except Exception as e:
            warnings.append(ValidationWarning(
                'root',
                f'Failed to analyze structure: {str(e)}',
                'analysis-failed',
                'warning'
            ))
        
        valid = len(errors) == 0
        
        return ValidationResult(
            valid=valid,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def validate_data(
        self,
        data: Any,
        options: Optional[LintOptions] = None
    ) -> ValidationResult:
        """Validate decoded data structure.
        
        Args:
            data: Decoded data to validate
            options: Validation options
            
        Returns:
            ValidationResult
        """
        if options is None:
            options = LintOptions()
        
        warnings = []
        suggestions = []
        
        try:
            stats = analyze(data)
            
            if options.max_depth and stats['depth'] > options.max_depth:
                warnings.append(ValidationWarning(
                    'root',
                    f"Nesting depth ({stats['depth']}) exceeds maximum",
                    'max-depth'
                ))
            
            if options.max_fields and stats['field_count'] > options.max_fields:
                warnings.append(ValidationWarning(
                    'root',
                    f"Field count exceeds maximum",
                    'max-fields'
                ))
        
        except Exception:
            pass
        
        return ValidationResult(
            valid=True,
            errors=[],
            warnings=warnings,
            suggestions=suggestions
        )


def validate_zon(zon_string: str, options: Optional[LintOptions] = None) -> ValidationResult:
    """Convenience function for validating ZON strings.
    
    Args:
        zon_string: ZON-encoded string
        options: Validation options
        
    Returns:
        ValidationResult
        
    Example:
        >>> result = validate_zon("name:Alice")
        >>> result.valid
        True
    """
    validator = ZonValidator()
    return validator.validate(zon_string, options)
