"""
Passive Scanner Implementation

This module re-exports the UnifiedPassiveScanner class which is now our primary
implementation for passive scanning.
"""

from scanning.passive.unified_scanner import UnifiedPassiveScanner as PassiveScanner

# For backward compatibility
__all__ = ['PassiveScanner']