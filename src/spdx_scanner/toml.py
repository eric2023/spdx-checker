"""
Minimal TOML implementation for SPDX Scanner.
This is a lightweight alternative to the toml package.
"""

import json
import re
from typing import Any, Dict, IO


def load(f: IO) -> Dict[str, Any]:
    """
    Load TOML from a file-like object.
    Simple implementation that handles basic key-value pairs and nested sections.
    """
    content = f.read()

    # Simple TOML parser for basic cases
    result: Dict[str, Any] = {}
    current_section = result
    section_stack = [result]

    for line in content.split('\n'):
        line = line.strip()

        # Skip empty lines and comments
        if not line or line.startswith('#'):
            continue

        # Handle section headers
        if line.startswith('[') and line.endswith(']'):
            section_name = line[1:-1].strip()

            # Handle nested sections like [tool.spdx-scanner]
            parts = section_name.split('.')
            current = result
            for part in parts:
                if part not in current:
                    current[part] = {}
                current = current[part]
            section_stack = [result] + [result.get(p, {}) for p in parts]
            current_section = current
            continue

        # Handle key-value pairs
        if '=' in line:
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()

            # Remove quotes if present
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]

            # Try to convert to appropriate type
            if value.lower() in ('true', 'false'):
                value = value.lower() == 'true'
            elif value.isdigit():
                value = int(value)
            else:
                try:
                    value = float(value)
                except ValueError:
                    pass  # Keep as string

            current_section[key] = value

    return result


def dump(data: Dict[str, Any], f: IO) -> None:
    """
    Write data to a TOML file.
    Simple implementation for basic dictionaries.
    """
    def format_value(value: Any) -> str:
        """Format a value for TOML output."""
        if isinstance(value, str):
            # Escape special characters and wrap in quotes
            value = value.replace('"', '\\"')
            return f'"{value}"'
        elif isinstance(value, bool):
            return str(value).lower()
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, list):
            return json.dumps(value)  # Use JSON array format for simplicity
        else:
            return str(value)

    lines = []

    def write_dict(d: Dict[str, Any], indent: int = 0) -> None:
        """Recursively write dictionary to TOML format."""
        for key, value in d.items():
            if isinstance(value, dict):
                # Check if all values are dicts (nested sections)
                if all(isinstance(v, dict) for v in d.values()):
                    # This is a section
                    lines.append('[' + '.'.join([key] + [''] * indent) + ']')
                    write_dict(value, indent + 1)
                else:
                    # This is a key-value pair
                    lines.append(' ' * indent + f'{key} = {format_value(value)}')
            elif isinstance(value, list):
                # For lists, write each value separately
                for item in value:
                    lines.append(' ' * indent + f'{key} = {format_value(item)}')
            else:
                lines.append(' ' * indent + f'{key} = {format_value(value)}')

    write_dict(data)
    f.write('\n'.join(lines))


# Re-export for compatibility
__all__ = ['load', 'dump']
