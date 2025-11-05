"""
LLM Client

Handles OpenAI API integration with error handling, retries, and fallbacks.
Supports mock mode for testing without API calls.
"""

import os
import json
import time
from typing import Dict, Any, Optional, List
from openai import OpenAI, OpenAIError, APITimeoutError, RateLimitError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class LLMClient:
    """
    LLM client with error handling, retries, and mock mode support.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize LLM client.
        
        Args:
            config: Optional configuration dictionary with keys:
                - model: str (default: "gpt-4o-mini")
                - temperature: float (default: 0.7)
                - max_tokens: int (default: 200)
                - timeout_seconds: int (default: 10)
                - retry_attempts: int (default: 2)
        """
        self.config = config or {}
        self.model = self.config.get('model', 'gpt-4o-mini')
        self.temperature = self.config.get('temperature', 0.7)
        self.max_tokens = self.config.get('max_tokens', 200)
        self.timeout = self.config.get('timeout_seconds', 10)
        self.retry_attempts = self.config.get('retry_attempts', 2)
        
        # Check if mock mode is enabled
        self.mock_mode = os.getenv('MOCK_LLM', 'false').lower() == 'true'
        
        if not self.mock_mode:
            # Initialize OpenAI client
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY not found in environment variables. "
                    "Please set it in your .env file or enable MOCK_LLM=true for testing."
                )
            self.client = OpenAI(api_key=api_key, timeout=self.timeout)
        else:
            self.client = None
            print("⚠ LLM Client running in MOCK mode (no API calls)")
    
    def generate(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate text using LLM with error handling and retries.
        
        Args:
            prompt: User prompt text
            system_message: Optional system message for context
            temperature: Optional override for temperature
            max_tokens: Optional override for max tokens
        
        Returns:
            Dictionary with keys:
                - success: bool
                - text: str (generated text or error message)
                - error: str or None
                - model: str
                - usage: dict or None
        """
        if self.mock_mode:
            return self._mock_generate(prompt)
        
        # Override defaults if provided
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens
        
        # Build messages
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        
        # Retry loop
        last_error = None
        for attempt in range(self.retry_attempts + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temp,
                    max_tokens=tokens
                )
                
                return {
                    'success': True,
                    'text': response.choices[0].message.content.strip(),
                    'error': None,
                    'model': self.model,
                    'usage': {
                        'prompt_tokens': response.usage.prompt_tokens,
                        'completion_tokens': response.usage.completion_tokens,
                        'total_tokens': response.usage.total_tokens
                    }
                }
                
            except APITimeoutError as e:
                last_error = f"API timeout after {self.timeout}s"
                if attempt < self.retry_attempts:
                    time.sleep(1)  # Brief pause before retry
                    continue
                    
            except RateLimitError as e:
                last_error = "Rate limit exceeded"
                if attempt < self.retry_attempts:
                    time.sleep(2)  # Longer pause for rate limits
                    continue
                    
            except OpenAIError as e:
                last_error = f"OpenAI API error: {str(e)}"
                break  # Don't retry on other OpenAI errors
                
            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
                break
        
        # All retries failed
        return {
            'success': False,
            'text': '',
            'error': last_error,
            'model': self.model,
            'usage': None
        }
    
    def _mock_generate(self, prompt: str) -> Dict[str, Any]:
        """
        Generate mock response for testing (no API call).
        
        Args:
            prompt: User prompt (used to tailor mock response)
        
        Returns:
            Mock response dictionary
        """
        # Simple mock responses based on prompt keywords
        if 'rationale' in prompt.lower():
            mock_text = "Based on your financial situation, this recommendation can help you optimize your approach and work toward your goals."
        elif 'actionable' in prompt.lower():
            mock_text = "Review your accounts and consider making adjustments based on your current financial priorities."
        elif 'relevant' in prompt.lower():
            mock_text = "This product may help address your current financial situation and support your goals."
        else:
            mock_text = "This is a mock LLM response for testing purposes."
        
        return {
            'success': True,
            'text': mock_text,
            'error': None,
            'model': 'mock',
            'usage': {'prompt_tokens': 50, 'completion_tokens': 20, 'total_tokens': 70}
        }


def load_config_from_file(config_path: str = 'config.json') -> Dict[str, Any]:
    """
    Load LLM configuration from config file.
    
    Args:
        config_path: Path to config.json
    
    Returns:
        LLM configuration dictionary
    """
    with open(config_path, 'r') as f:
        config = json.load(f)
    return config.get('llm', {})


# Convenience functions for common use cases

def generate_rationale(
    user_context: Dict[str, Any],
    content_title: str,
    persona_name: str,
    client: Optional[LLMClient] = None
) -> str:
    """
    Generate a rationale for why educational content is relevant.
    
    Args:
        user_context: Dictionary with user metrics
        content_title: Title of educational content
        persona_name: Name of persona
        client: Optional LLMClient instance (creates new one if None)
    
    Returns:
        Rationale text (or fallback if generation fails)
    """
    if client is None:
        try:
            config = load_config_from_file()
            client = LLMClient(config)
        except Exception as e:
            return _fallback_rationale(persona_name, content_title)
    
    # Build prompt (will be defined in prompts.py)
    prompt = f"""Generate a brief rationale (under 100 words) for why "{content_title}" is relevant to a user with {persona_name} persona.

User metrics: {json.dumps(user_context, indent=2)}

Use empowering language, cite specific numbers from metrics, and focus on benefits."""
    
    system_message = "You are a financial education assistant helping users understand personalized recommendations."
    
    result = client.generate(prompt, system_message)
    
    if result['success']:
        return result['text']
    else:
        print(f"⚠ LLM generation failed: {result['error']}, using fallback")
        return _fallback_rationale(persona_name, content_title)


def generate_actionable_items(
    user_context: Dict[str, Any],
    persona_name: str,
    count: int = 2,
    client: Optional[LLMClient] = None
) -> List[Dict[str, str]]:
    """
    Generate actionable items for a user.
    
    Args:
        user_context: Dictionary with user metrics
        persona_name: Name of persona
        count: Number of items to generate (1-3)
        client: Optional LLMClient instance
    
    Returns:
        List of dicts with 'text' and 'rationale' keys
    """
    if client is None:
        try:
            config = load_config_from_file()
            client = LLMClient(config)
        except Exception as e:
            return _fallback_actionable_items(persona_name, count)
    
    prompt = f"""Generate {count} specific, actionable next steps for a user with {persona_name} persona.

User metrics: {json.dumps(user_context, indent=2)}

Each action should be:
- Specific and measurable
- Achievable (small steps)
- Cite actual numbers from metrics
- Use empowering language ("you might consider", not "you should")

Return as JSON array: [{{"text": "action text", "rationale": "why this helps"}}]"""
    
    system_message = "You are a financial education assistant. Return valid JSON only."
    
    result = client.generate(prompt, system_message, max_tokens=300)
    
    if result['success']:
        try:
            # Try to parse JSON
            items = json.loads(result['text'])
            if isinstance(items, list) and all('text' in item and 'rationale' in item for item in items):
                return items[:count]  # Limit to requested count
        except json.JSONDecodeError:
            pass
    
    print(f"⚠ LLM generation failed or invalid JSON, using fallback")
    return _fallback_actionable_items(persona_name, count)


def _fallback_rationale(persona_name: str, content_title: str) -> str:
    """Fallback rationale when LLM fails."""
    return f"Based on your {persona_name} profile, this content may be helpful for your situation."


def _fallback_actionable_items(persona_name: str, count: int) -> List[Dict[str, str]]:
    """Fallback actionable items when LLM fails."""
    fallbacks = {
        "High Utilization": [
            {
                "text": "Review your credit card statements to identify which cards have the highest interest rates",
                "rationale": "Focusing on high-interest debt first can help you save money on interest charges."
            },
            {
                "text": "Consider setting up automatic minimum payments to protect your credit score",
                "rationale": "Automating payments helps ensure you never miss a due date."
            }
        ],
        "Variable Income Budgeter": [
            {
                "text": "Calculate your average monthly income over the past 6 months",
                "rationale": "Understanding your average income helps create a sustainable budget."
            },
            {
                "text": "Set aside a percentage during high-earning months",
                "rationale": "Building a buffer during good months reduces stress during lean times."
            }
        ],
        "Subscription-Heavy": [
            {
                "text": "Review your bank statements from the past 3 months to identify all recurring charges",
                "rationale": "A thorough audit often reveals forgotten subscriptions."
            },
            {
                "text": "Choose 2-3 services you value most and consider canceling the rest",
                "rationale": "Prioritizing helps you cut spending without sacrificing value."
            }
        ],
        "Savings Builder": [
            {
                "text": "Review your current savings account interest rate",
                "rationale": "High-yield accounts offer significantly better returns."
            },
            {
                "text": "Set up automatic transfers from checking to savings",
                "rationale": "Automation ensures consistent savings without relying on willpower."
            }
        ],
        "Cash Flow Stressed": [
            {
                "text": "Try to set aside $25-50 from your next paycheck",
                "rationale": "Even a small buffer can help break the paycheck-to-paycheck cycle."
            },
            {
                "text": "Create a list of all your bills and their due dates",
                "rationale": "Strategic timing of payments can help maintain higher balances."
            }
        ]
    }
    
    items = fallbacks.get(persona_name, [
        {
            "text": "Review your financial accounts and recent transactions",
            "rationale": "Understanding your current situation is the first step to improvement."
        }
    ])
    
    return items[:count]

