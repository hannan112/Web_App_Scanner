# scanning/integrations/base_adapter.py

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class BaseAdapter:
    """Base class for all scanner adapters"""

    def __init__(self, config=None):
        self.config = config or {}
        self.name = "BaseAdapter"

    def _log_error(self, message: str, exception: Optional[Exception] = None):
        """Log error with consistent format"""
        if exception:
            logger.error(f"[{self.name}] {message}: {str(exception)}")
        else:
            logger.error(f"[{self.name}] {message}")

    def _log_info(self, message: str):
        """Log info with consistent format"""
        logger.info(f"[{self.name}] {message}")

    def is_available(self) -> Dict[str, Any]:
        """
        Check if the tool is available for use

        Returns:
            Dict with keys:
                available (bool): Whether the tool is available
                error (str, optional): Error message if not available
        """
        return {"available": False, "error": "Not implemented"}

    def _create_error_finding(self, error_message: str, url: str) -> Dict[str, Any]:
        """
        Create a standard error finding when a tool fails

        Args:
            error_message (str): Error message to include
            url (str): URL that was being scanned

        Returns:
            Dict: Standard error finding
        """
        return {
            "name": f"{self.name} Error",
            "description": f"Error using {self.name}: {error_message}",
            "severity": "info",
            "url": url,
            "confidence": 1.0,
            "source": self.name,
        }
