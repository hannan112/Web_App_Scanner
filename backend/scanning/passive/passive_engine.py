"""
Engine for coordinating passive scanning operations
"""
import logging
from scanning.passive.unified_scanner import UnifiedPassiveScanner

logger = logging.getLogger(__name__)

# Re-export UnifiedPassiveScanner class
__all__ = ['UnifiedPassiveScanner']