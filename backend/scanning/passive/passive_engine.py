"""
Engine for coordinating passive scanning operations
"""
import logging
from scanning.passive.passive_scanner import PassiveScanner

logger = logging.getLogger(__name__)

# Re-export PassiveScanner class
__all__ = ['PassiveScanner']