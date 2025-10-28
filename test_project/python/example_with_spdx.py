#!/usr/bin/env python3
"""
SPDX-License-Identifier: MIT

Copyright (c) 2025 Example Corporation
"""

import json
import sys


class ExampleClass:
    """Example class for testing SPDX scanner."""

    def __init__(self, name: str):
        self.name = name

    def get_name(self) -> str:
        """Get the name of the instance."""
        return self.name


def main():
    """Main function."""
    print("Hello, SPDX Scanner!")
    example = ExampleClass("test")
    print(f"Name: {example.get_name()}")


if __name__ == "__main__":
    main()