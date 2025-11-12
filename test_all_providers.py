"""Test all providers (Gemini, OpenAI, Grok) to verify they work"""
import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# API keys should be set via environment variables:
# export GEMINI_API_KEY='your-key'
# export OPENAI_API_KEY='your-key'
# export XAI_API_KEY='your-key'

if 'GEMINI_API_KEY' not in os.environ:
    logger.error("GEMINI_API_KEY not set!")
    sys.exit(1)
if 'OPENAI_API_KEY' not in os.environ:
    logger.error("OPENAI_API_KEY not set!")
    sys.exit(1)
if 'XAI_API_KEY' not in os.environ:
    logger.error("XAI_API_KEY not set!")
    sys.exit(1)

from providers.gemini import GeminiModelProvider
from providers.openai import OpenAIModelProvider
from providers.xai import XAIModelProvider

def test_provider(name, provider_class, api_key, model_name):
    """Test a single provider"""
    logger.info("=" * 80)
    logger.info(f"Testing {name}")
    logger.info("=" * 80)

    try:
        provider = provider_class(api_key=api_key)
        logger.info(f"✓ Provider initialized")

        response = provider.generate_content(
            prompt="Say hello and tell me what 2+2 equals.",
            model_name=model_name,
            temperature=0.3
        )

        logger.info(f"✓ API call successful!")
        logger.info(f"  Model: {response.model_name}")
        logger.info(f"  Response: {response.content[:100]}...")
        logger.info(f"  Tokens: {response.usage.get('total_tokens', 'N/A')}")
        return True

    except Exception as e:
        logger.error(f"✗ {name} FAILED")
        logger.error(f"  Error: {str(e)[:200]}")
        return False

def main():
    """Test all providers"""
    results = {}

    # Test Gemini
    results['Gemini'] = test_provider(
        name="Gemini (gemini-2.5-flash)",
        provider_class=GeminiModelProvider,
        api_key=os.environ['GEMINI_API_KEY'],
        model_name="gemini-2.5-flash"
    )

    # Test OpenAI
    results['OpenAI'] = test_provider(
        name="OpenAI (gpt-4o-mini)",
        provider_class=OpenAIModelProvider,
        api_key=os.environ['OPENAI_API_KEY'],
        model_name="gpt-4o-mini"
    )

    # Test Grok/xAI
    results['Grok'] = test_provider(
        name="Grok (grok-4)",
        provider_class=XAIModelProvider,
        api_key=os.environ['XAI_API_KEY'],
        model_name="grok-4"
    )

    # Summary
    logger.info("=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)
    for provider, success in results.items():
        status = "✓ WORKING" if success else "✗ FAILED"
        logger.info(f"{provider:15} {status}")

    logger.info("=" * 80)

    all_working = all(results.values())
    if all_working:
        logger.info("🎉 ALL PROVIDERS WORKING!")
    else:
        logger.warning("⚠️  Some providers failed - see errors above")

    return all_working

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
