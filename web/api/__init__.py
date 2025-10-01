"""
API package for Ultra-Turbo AppData Cleaner Web Interface
"""

from .system import SystemAPI
from .scanner import ScannerAPI
from .cleaner import CleanerAPI

__all__ = ['SystemAPI', 'ScannerAPI', 'CleanerAPI']