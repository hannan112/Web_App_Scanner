import logging

import requests
from Wappalyzer import Wappalyzer, WebPage

logger = logging.getLogger(__name__)


def test_wappalyzer_integration():
    """Test Wappalyzer integration"""
    logger.info("Testing Wappalyzer integration...")

    try:
        # Initialize Wappalyzer
        wappalyzer = Wappalyzer.latest()
        logger.info("Wappalyzer initialized successfully")

        # Create webpage object
        url = "https://example.com/"
        logger.info(f"Requesting {url}...")
        response = requests.get(url)
        logger.info(f"Got response with status code: {response.status_code}")

        webpage = WebPage.new_from_response(response)
        logger.info("Created WebPage object")

        # Analyze
        logger.info("Analyzing with Wappalyzer...")
        result = wappalyzer.analyze(webpage)
        logger.info(f"Detected technologies: {result}")
        logger.info("Test completed successfully!")

        return result

    except Exception as e:
        logger.error(f"Error in Wappalyzer test: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return None


if __name__ == "__main__":
    # Set up logging for standalone execution
    logging.basicConfig(level=logging.INFO)
    test_wappalyzer_integration()
