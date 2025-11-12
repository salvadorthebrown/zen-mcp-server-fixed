#!/usr/bin/env python
"""Test script to debug Gemini provider API key issue"""
import sys
from providers.gemini import GeminiModelProvider
from utils.env import get_env

# Get API key
api_key = get_env("GEMINI_API_KEY")
print(f"API key from get_env(): {api_key[:20]}..." if api_key else "None")

# Create provider
provider = GeminiModelProvider(api_key=api_key)
print(f"Provider api_key attribute: {provider.api_key[:20]}..." if provider.api_key else "None")

# Try to generate content
try:
    response = provider.generate_content(
        prompt="Say hello",
        model_name="gemini-2.5-flash",
        temperature=0.3
    )
    print(f"SUCCESS: {response.content[:100]}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
