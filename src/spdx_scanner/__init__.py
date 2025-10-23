"""
SPDX Scanner - Automatic SPDX license declaration scanner and corrector.

This package provides tools for scanning source code files, detecting SPDX license
declarations, and automatically correcting or completing missing license information
according to SPDX specification standards.
"""

__version__ = "0.1.0"
__author__ = "SPDX Scanner Team"
__email__ = "team@example.com"
__description__ = "Automatic SPDX license declaration scanner and corrector for source code files"

from .models import SPDXInfo, FileInfo, ValidationResult, CorrectionResult
from .scanner import FileScanner
from .parser import SPDXParser
from .validator import SPDXValidator
from .corrector import SPDXCorrector
from .reporter import Reporter
from .config import Configuration

__all__ = [
    "SPDXInfo",
    "FileInfo",
    "ValidationResult",
    "CorrectionResult",
    "FileScanner",
    "SPDXParser",
    "SPDXValidator",
    "SPDXCorrector",
    "Reporter",
    "Configuration",
]