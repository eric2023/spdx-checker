"""
Entry point for running SPDX Scanner as a module.

This allows running the scanner with: python -m spdx_scanner
"""

from .cli import main

if __name__ == "__main__":
    main()