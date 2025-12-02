"""OpenAI SDK wrapper for automatic ZON format handling."""

import re
from typing import Any, Optional, Dict, List, Union
from zon import decode

try:
    from openai import OpenAI
    from openai.types.chat import ChatCompletion
except ImportError:
    OpenAI = None
    ChatCompletion = None

class ZOpenAI:
    """OpenAI client wrapper with automatic ZON format handling.
    
    Automatically injects ZON format instructions and parses responses.
    """
    def __init__(self, client: Any):
        """Initialize with an OpenAI client.
        
        Args:
            client: OpenAI client instance
            
        Raises:
            ImportError: If openai package is not installed
        """
        if OpenAI is None:
            raise ImportError("The 'openai' package is required for ZOpenAI.")
        self.client = client

    def chat(self, **kwargs) -> Any:
        """Send chat completion request with automatic ZON parsing.
        
        Automatically appends ZON format instructions to system prompt
        and parses the response.
        
        Args:
            **kwargs: Arguments to pass to OpenAI chat.completions.create
            
        Returns:
            Parsed ZON data structure
        """
        messages = list(kwargs.get('messages', []))
        
        instructions = """

RESPONSE FORMAT: You must respond in ZON (Zero Overhead Notation).
Rules:
1. Use 'key:value' for properties.
2. Use 'key{...}' for nested objects.
3. Use 'key[...]' for arrays.
4. Use '@(N):col1,col2' for tables.
5. Use 'T'/'F' for booleans, 'null' for null.
6. Do NOT wrap in markdown code blocks."""

        system_msg_idx = -1
        for i, msg in enumerate(messages):
            if msg.get('role') == 'system':
                system_msg_idx = i
                break
        
        if system_msg_idx != -1:
            messages[system_msg_idx]['content'] += instructions
        else:
            messages.insert(0, {'role': 'system', 'content': instructions})
            
        kwargs['messages'] = messages
        kwargs['stream'] = False
        
        response = self.client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content or ''
        
        cleaned = re.sub(r'```(zon|zonf)?', '', content).strip()
        cleaned = cleaned.replace('```', '').strip()
        
        return decode(cleaned)

def create_zopenai(api_key: Optional[str] = None) -> ZOpenAI:
    """Create a ZOpenAI instance.
    
    Args:
        api_key: Optional OpenAI API key
        
    Returns:
        ZOpenAI wrapper instance
        
    Raises:
        ImportError: If openai package is not installed
    """
    if OpenAI is None:
        raise ImportError("The 'openai' package is required for ZOpenAI.")
    return ZOpenAI(OpenAI(api_key=api_key))
