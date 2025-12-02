"""Azure OpenAI client for querying multiple LLM models with caching."""

import os
import json
import hashlib
import time
import random
from pathlib import Path
from typing import Dict, Any, Optional
from openai import AzureOpenAI, APIError, RateLimitError

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

CACHE_DIR = os.environ.get('CACHE_DIR', os.path.join(os.path.dirname(__file__), '../../.cache'))
USE_CACHE = True

if USE_CACHE and not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR, exist_ok=True)

class AzureAIClient:
    """Azure OpenAI client for querying multiple LLM models.
    
    Provides methods to query various Azure-deployed models with automatic
    caching, retry logic for rate limits, and parallel query support.
    """
    def __init__(self):
        """Initialize the Azure AI client.
        
        Raises:
            ValueError: If required environment variables are not set
        """
        if not os.environ.get('AZURE_OPENAI_API_KEY'):
            raise ValueError('AZURE_OPENAI_API_KEY not set in environment')
        if not os.environ.get('AZURE_OPENAI_ENDPOINT'):
            raise ValueError('AZURE_OPENAI_ENDPOINT not set in environment')
            
        self.client = AzureOpenAI(
            api_key=os.environ['AZURE_OPENAI_API_KEY'],
            azure_endpoint=os.environ['AZURE_OPENAI_ENDPOINT'],
            api_version=os.environ.get('AZURE_OPENAI_API_VERSION', '2024-02-01')
        )
        
        self.models = {
            'gpt-5-nano': os.environ.get('AZURE_GPT5_DEPLOYMENT', 'gpt-5-nano'),
            'grok-3': os.environ.get('AZURE_GROK3_DEPLOYMENT', 'grok-3'),
            'deepseek-v3.1': os.environ.get('AZURE_DEEPSEEK_DEPLOYMENT', 'DeepSeek-V3.1'),
            'Llama-3.3-70B-Instruct': os.environ.get('AZURE_LLAMA33_DEPLOYMENT', 'Llama-3.3-70B-Instruct')
        }
        
        print(f"✅ Azure AI client initialized")
        print(f"   Endpoint: {os.environ['AZURE_OPENAI_ENDPOINT']}")
        print(f"   Models: {', '.join(self.models.keys())}")

    def _get_cache_key(self, model: str, prompt: str) -> str:
        """Generate cache key for a query.
        
        Args:
            model: Model name
            prompt: Query prompt
            
        Returns:
            Path to cache file
        """
        hash_obj = hashlib.md5(f"{model}:{prompt}".encode('utf-8'))
        return os.path.join(CACHE_DIR, f"{hash_obj.hexdigest()}.json")

    def _get_cache(self, model: str, prompt: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached response if available.
        
        Args:
            model: Model name
            prompt: Query prompt
            
        Returns:
            Cached response dict or None if not cached
        """
        if not USE_CACHE:
            return None
            
        cache_file = self._get_cache_key(model, prompt)
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    def _set_cache(self, model: str, prompt: str, response: Dict[str, Any]):
        """Save response to cache.
        
        Args:
            model: Model name
            prompt: Query prompt
            response: Response dict to cache
        """
        if not USE_CACHE:
            return
            
        cache_file = self._get_cache_key(model, prompt)
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(response, f, indent=2)
        except Exception as e:
            print(f"Failed to cache response: {e}")

    def query(self, model_name: str, prompt: str, max_tokens: int = 2000) -> Dict[str, Any]:
        """Query a model with a prompt.
        
        Includes automatic retry logic for rate limits with exponential backoff.
        
        Args:
            model_name: Name of the model to query
            prompt: The prompt text
            max_tokens: Maximum tokens in response
            
        Returns:
            Dict with 'answer', 'tokensUsed', and 'cached' keys
            
        Raises:
            ValueError: If model name is unknown
            RateLimitError: If rate limit exhausted after retries
        """
        cached = self._get_cache(model_name, prompt)
        if cached:
            return {
                'answer': cached['answer'],
                'tokensUsed': cached['tokensUsed'],
                'cached': True
            }
            
        deployment = self.models.get(model_name)
        if not deployment:
            raise ValueError(f"Unknown model: {model_name}. Available: {', '.join(self.models.keys())}")
            
        max_retries = 15
        retries = 0
        
        while retries <= max_retries:
            try:
                response = self.client.chat.completions.create(
                    model=deployment,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a data analyst. Answer questions about provided data accurately and concisely. Provide only the direct answer without explanation."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_tokens=max_tokens
                )
                
                answer = response.choices[0].message.content.strip() if response.choices else ""
                tokens_used = response.usage.total_tokens if response.usage else 0
                
                result = {'answer': answer, 'tokensUsed': tokens_used}
                
                if answer:
                    self._set_cache(model_name, prompt, result)
                    
                result['cached'] = False
                return result
                
            except RateLimitError:
                if retries < max_retries:
                    retries += 1
                    delay = (2 ** retries) * 1 + (random.random() * 1)
                    if delay > 60:
                        delay = 60
                    print(f"      ⚠️  Rate limit hit for {model_name}. Retrying in {delay:.1f}s (Attempt {retries}/{max_retries})...")
                    time.sleep(delay)
                    continue
                raise
            except Exception as e:
                print(f"Error querying {model_name}: {e}")
                raise

    def query_all(self, prompt: str, max_tokens: int = 100) -> Dict[str, Any]:
        """Query all configured models with the same prompt.
        
        Args:
            prompt: The prompt text
            max_tokens: Maximum tokens in response
            
        Returns:
            Dict mapping model names to their responses
        """
        results = {}
        for model_name in self.models:
            try:
                results[model_name] = self.query(model_name, prompt, max_tokens)
            except Exception as e:
                results[model_name] = {
                    'answer': None,
                    'tokensUsed': 0,
                    'error': str(e)
                }
        return results

if __name__ == "__main__":
    print("🔬 Azure AI Client Test\n")
    print("═" * 60)
    
    try:
        client = AzureAIClient()
        
        test_prompt = """Data format: JSON
Data:
[
  {"id": 1, "name": "Alice", "salary": 95000},
  {"id": 2, "name": "Bob", "salary": 82000}
]

Question: What is Alice's salary?

Answer:"""
        
        print("\n📝 Test Prompt:")
        print(test_prompt[:200] + "...\n")
        
        print("Querying models...\n")
        
        results = client.query_all(test_prompt)
        
        for model, result in results.items():
            if result.get('error'):
                print(f"❌ {model}: Error - {result['error']}")
            else:
                cache_status = "💾 (cached)" if result.get('cached') else "🌐 (live)"
                print(f"✅ {model} {cache_status}:")
                print(f"   Answer: \"{result['answer']}\"")
                print(f"   Tokens: {result['tokensUsed']}")
                
        print("\n" + "═" * 60)
        print("✨ Test complete!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("\nMake sure you have:")
        print("1. Created .env file")
        print("2. Set AZURE_OPENAI_API_KEY")
        print("3. Set AZURE_OPENAI_ENDPOINT")
        print("4. Set model deployment names")
