"""Debug script to test Gemini provider directly"""
import os
import sys
import logging

# Set up verbose logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add zen to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# API key should be set via environment variable:
# export GEMINI_API_KEY='your-key'

if 'GEMINI_API_KEY' not in os.environ:
    logger.error("GEMINI_API_KEY not set! Set it with: export GEMINI_API_KEY='your-key'")
    sys.exit(1)

from providers.gemini import GeminiModelProvider

def test_gemini():
    """Test Gemini provider with debug logging"""
    logger.info("=" * 80)
    logger.info("Testing Gemini Provider")
    logger.info("=" * 80)

    api_key = os.environ['GEMINI_API_KEY']
    logger.info(f"API Key (first 20 chars): {api_key[:20]}...")
    logger.info(f"API Key length: {len(api_key)}")
    logger.info(f"API Key type: {type(api_key)}")

    # Initialize provider
    logger.info("Initializing GeminiModelProvider...")
    provider = GeminiModelProvider(api_key=api_key)

    # Get available models
    logger.info("Getting available models...")
    capabilities = provider.get_all_model_capabilities()
    logger.info(f"Available models: {list(capabilities.keys())}")

    # Test a simple call
    logger.info("=" * 80)
    logger.info("Making test API call to gemini-2.5-pro...")
    logger.info("=" * 80)

    try:
        response = provider.generate_content(
            prompt="Say hello and confirm you are Gemini 2.5 Pro. What is 2+2?",
            model_name="gemini-2.5-pro",
            temperature=0.3
        )
        logger.info("=" * 80)
        logger.info("SUCCESS!")
        logger.info("=" * 80)
        logger.info(f"Response content: {response.content}")
        logger.info(f"Model name: {response.model_name}")
        logger.info(f"Usage: {response.usage}")

    except Exception as e:
        logger.error("=" * 80)
        logger.error("FAILED!")
        logger.error("=" * 80)
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.exception("Full traceback:")

        # Try to extract more details
        if hasattr(e, '__dict__'):
            logger.error(f"Error attributes: {e.__dict__}")

if __name__ == "__main__":
    test_gemini()
