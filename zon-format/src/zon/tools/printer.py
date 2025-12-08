"""ZON Pretty Printer

Formats ZON strings with indentation and newlines for readability.
"""

from typing import Optional


def expand_print(zon: str, indent_size: int = 2) -> str:
    """Expand ZON string with whitespace for readability.
    
    Adds indentation and newlines to nested objects and arrays
    to match TypeScript readable mode formatting.
    
    Args:
        zon: ZON-encoded string
        indent_size: Number of spaces per indentation level
        
    Returns:
        Formatted ZON string with indentation
        
    Example:
        >>> zon = "metadata{generated:2025-01-01,source:A}"
        >>> print(expand_print(zon))
        metadata: {
          generated:2025-01-01
          source:A
        }
    """
    indent_str = ' ' * indent_size
    result = ''
    indent = 0
    in_string = False
    in_table = False
    table_brace_balance = 0
    table_bracket_balance = 0
    context_stack = []  # Tracks 'array', 'object', or 'object-flat'
    
    i = 0
    while i < len(zon):
        char = zon[i]
        prev = zon[i - 1] if i > 0 else ''
        
        # Track if we're inside a string
        if char == '"' and prev != '\\':
            in_string = not in_string
        
        if in_string:
            result += char
            i += 1
            continue
        
        # Check for table start
        if char == '@' and not in_string:
            in_table = True
            table_brace_balance = 0
            table_bracket_balance = 0
        
        # Check for potential inline block (only if not in table)
        if not in_table and (char == '{' or char == '[') and indent < 20:
            is_array = char == '['
            parent_context = context_stack[-1] if context_stack else None
            
            if is_array or parent_context == 'array':
                closing_char = '}' if char == '{' else ']'
                j = i + 1
                depth = 1
                length = 0
                has_nested = False
                
                while j < len(zon) and length < 60:
                    if zon[j] in ('{', '['):
                        has_nested = True
                        depth += 1
                    elif zon[j] in ('}', ']'):
                        depth -= 1
                    
                    if depth == 0:
                        break
                    length += 1
                    j += 1
                
                # If block is short and flat, keep it inline
                if depth == 0 and length < 60 and not has_nested:
                    # Ensure colon before inline array if following a key
                    if is_array and result.strip() and not result.rstrip().endswith(':') and not result.rstrip().endswith(',') and not result.rstrip().endswith('\n'):
                        result += ':'
                    
                    block = zon[i:j+1]
                    result += block
                    i = j
                    i += 1
                    continue
        
        # Handle different characters
        if char == '{':
            # Check if empty object
            next_char_obj = ''
            for k in range(i+1, len(zon)):
                if not zon[k].isspace():
                    next_char_obj = zon[k]
                    break
            
            if next_char_obj == '}':
                # Empty object: print {} inline
                if result.strip() and not result.rstrip().endswith(':') and not result.rstrip().endswith(',') and not result.rstrip().endswith('\n') and not result.rstrip().endswith('['):
                    result += ':'
                result += '{}'
                # Skip to closing brace
                while i < len(zon) and zon[i] != '}':
                    i += 1
                i += 1
                continue
            
            if in_table:
                table_brace_balance += 1
                result += '{'
            else:
                # Check if we are inside an array
                parent_context = context_stack[-1] if context_stack else None
                
                if parent_context == 'array':
                    # Flattened object in array
                    context_stack.append('object-flat')
                else:
                    # Standard object
                    context_stack.append('object')
                    
                    # Only increment indent if NOT root object
                    if result.strip():
                        # If previous char was not colon, add one
                        if not result.rstrip().endswith(':') and not result.rstrip().endswith(',') and not result.rstrip().endswith('[') and not result.rstrip().endswith('{'):
                            result += ':'
                        
                        # Add brace (no space before brace for decoder compatibility)
                        result += '{'
                        indent += 1
                        result += '\n' + indent_str * indent
                    else:
                        # Root object
                        result += '{'
                        indent += 1
                        result += '\n' + indent_str * indent
        
        elif char == '[':
            # Check if empty array
            next_char_arr = ''
            for k in range(i+1, len(zon)):
                if not zon[k].isspace():
                    next_char_arr = zon[k]
                    break
            
            if next_char_arr == ']':
                # Empty array: print [] inline
                if result.strip() and not result.rstrip().endswith(':') and not result.rstrip().endswith(',') and not result.rstrip().endswith('\n') and not result.rstrip().endswith('['):
                    result += ':'
                result += '[]'
                # Skip to closing bracket
                while i < len(zon) and zon[i] != ']':
                    i += 1
                i += 1
                continue
            
            if in_table:
                table_bracket_balance += 1
                result += '['
            else:
                context_stack.append('array')
                # Ensure colon before array if following a key
                if result.strip() and not result.rstrip().endswith(':') and not result.rstrip().endswith(',') and not result.rstrip().endswith('\n') and not result.rstrip().endswith('['):
                    result += ':'
                indent += 1
                # Start first item with dash
                result += '\n' + indent_str * indent + '- '
        
        elif char == '}':
            if in_table:
                if table_brace_balance > 0:
                    table_brace_balance -= 1
                    result += '}'
                else:
                    in_table = False
            else:
                current_context = context_stack.pop() if context_stack else None
                
                if current_context == 'object':
                    indent -= 1
                    result += '\n' + indent_str * indent + '}'
                # If object-flat, do nothing (no dedent, no brace)
        
        elif char == ']':
            if in_table:
                if table_bracket_balance > 0:
                    table_bracket_balance -= 1
                    result += ']'
                else:
                    in_table = False
            else:
                # If we are closing the array, we might need to pop a pending object-flat first
                if context_stack and context_stack[-1] == 'object-flat':
                    context_stack.pop()
                if context_stack:
                    context_stack.pop()
                indent -= 1
                # No character, just dedent
        
        elif char == ',':
            if in_table:
                result += char
            else:
                # Check context to decide separator
                top_context = context_stack[-1] if context_stack else None
                
                if top_context == 'array':
                    # Between array items: Use newline and dash
                    result += '\n' + indent_str * indent + '- '
                else:
                    # Between object fields: Use single newline (no comma)
                    result += '\n' + indent_str * indent
        
        elif char == '\n':
            if in_table:
                result += '\n' + indent_str * indent
            else:
                result += char
        
        elif char == ':':
            if in_table:
                result += char
            else:
                result += ':'  # No space after colon
        
        else:
            # Preserve all characters including spaces
            result += char
        
        i += 1
    
    return result


def compact_print(zon: str) -> str:
    """Compact ZON string by removing extra whitespace.
    
    Args:
        zon: ZON-encoded string
        
    Returns:
        Compacted ZON string
        
    Example:
        >>> zon = "metadata: {\\n  key: value\\n}"
        >>> compact_print(zon)
        'metadata:{key:value}'
    """
    import re
    return (zon
        .replace('\n', ' ')  # Remove newlines
        .replace('\r', '')   # Remove carriage returns
        # Collapse multiple spaces
        # But be careful with strings
    )
    # Simple implementation - just remove extra whitespace
    result = re.sub(r'\n\s*', ' ', zon)
    result = re.sub(r'\s+', ' ', result)
    result = re.sub(r',\s+', ',', result)
    result = re.sub(r':\s+', ':', result)
    return result.strip()
