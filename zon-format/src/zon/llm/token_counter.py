"""Token counting utility for estimating LLM token usage."""

import math

class TokenCounter:
    """Simple token counter using character-based estimation.
    
    Estimates token count as approximately 1 token per 4 characters,
    which is a common approximation for many LLM tokenization schemes.
    """
    
    def count(self, text: str) -> int:
        """Count tokens in text using character-based estimation.
        
        Args:
            text: The text to count tokens for
            
        Returns:
            Estimated token count (characters / 4, rounded up)
        """
        if not text:
            return 0
        return math.ceil(len(text) / 4)

    def count_for_model(self, text: str, model: str) -> int:
        """Count tokens for a specific model.
        
        Currently uses the same generic estimation regardless of model.
        
        Args:
            text: The text to count tokens for
            model: Model name (currently unused)
            
        Returns:
            Estimated token count
        """
        return self.count(text)
