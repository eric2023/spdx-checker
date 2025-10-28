"""
Minimal pathspec implementation for SPDX Scanner.
This is a lightweight alternative to the pathspec package.
"""

import os
import glob
from pathlib import Path
from typing import List, Iterable, Generator


class PathSpec:
    """A simple path specification matcher."""

    def __init__(self, patterns: List[str]):
        """Initialize with a list of patterns."""
        self.patterns = patterns

    @classmethod
    def from_lines(cls, format_name: str, lines: Iterable[str]) -> 'PathSpec':
        """Create PathSpec from lines of patterns."""
        return cls([line.strip() for line in lines if line.strip()])

    def match_file(self, filepath: str) -> bool:
        """Check if filepath matches any pattern."""
        # Simple glob matching
        for pattern in self.patterns:
            if self._match_pattern(filepath, pattern):
                return True
        return False

    def _match_pattern(self, filepath: str, pattern: str) -> bool:
        """Check if filepath matches a single pattern."""
        # Convert glob pattern to regex
        # Handle **/* pattern
        if pattern.startswith('**/'):
            # Match anywhere in the path
            pattern_part = pattern[3:]
            # Use fnmatch for simple glob matching
            import fnmatch
            return fnmatch.fnmatch(filepath, f'*{pattern_part}')
        else:
            # Match from beginning or end
            import fnmatch
            if pattern.startswith('*'):
                # Ends with pattern
                return filepath.endswith(pattern[1:])
            elif pattern.endswith('*'):
                # Starts with pattern
                return filepath.startswith(pattern[:-1])
            else:
                # Exact match or glob
                return fnmatch.fnmatch(filepath, pattern)


class GitWildMatch:
    """Git wildmatch pattern matching."""

    @staticmethod
    def match_file(filepath: str, pattern: str) -> bool:
        """Match file against git wildmatch pattern."""
        # Simplified implementation
        # Convert git pattern to simple glob
        import fnmatch

        # Handle ** pattern (any number of directories)
        if '**' in pattern:
            parts = pattern.split('**')
            if len(parts) == 2:
                prefix, suffix = parts
                return fnmatch.fnmatch(filepath, f'*{suffix}')

        # Handle * pattern (any characters except /)
        # Handle ? pattern (any single character)
        regex_pattern = pattern.replace('.', r'\.')
        regex_pattern = regex_pattern.replace('*', '.*')
        regex_pattern = regex_pattern.replace('?', '.')

        import re
        return bool(re.match(f'^{regex_pattern}$', filepath))


# Re-export for compatibility
__all__ = ['PathSpec']
