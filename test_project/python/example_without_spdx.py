#!/usr/bin/env python3
"""
This is a sample Python file without SPDX license declaration.
We'll use this to test the scanner's ability to find missing declarations.
"""

import os
import sys


def calculate_sum(a, b):
    """Calculate the sum of two numbers."""
    return a + b


def main():
    """Main function."""
    result = calculate_sum(10, 20)
    print(f"The sum is: {result}")
    print(f"Python version: {sys.version}")


if __name__ == "__main__":
    main()