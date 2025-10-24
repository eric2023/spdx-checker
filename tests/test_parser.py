"""
Tests for SPDX Scanner parser component.
"""

import re
import pytest
from spdx_scanner.parser import SPDXParser, SPDXPatterns, create_default_parser
from spdx_scanner.models import SPDXInfo, SPDXDeclarationType, ValidationError, ValidationSeverity
from unittest.mock import Mock, patch


class TestSPDXPatterns:
    """Test SPDX patterns."""

    def test_license_identifier_patterns(self):
        """Test license identifier pattern matching."""
        patterns = SPDXPatterns()

        # Test various license identifier formats
        test_cases = [
            ("SPDX-License-Identifier: MIT", "MIT"),
            ("spdx-license-identifier: Apache-2.0", "Apache-2.0"),
            ("SPDX-License-Identifier : GPL-3.0", "GPL-3.0"),
            ("// SPDX-License-Identifier: BSD-3-Clause", "BSD-3-Clause"),
            ("# SPDX-License-Identifier: GPL-2.0+", "GPL-2.0+"),
        ]

        for text, expected_license in test_cases:
            for pattern in patterns.LICENSE_IDENTIFIER_PATTERNS:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    assert match.group(1) == expected_license
                    break
            else:
                pytest.fail(f"No pattern matched: {text}")

    def test_copyright_patterns(self):
        """Test copyright pattern matching."""
        patterns = SPDXPatterns()

        test_cases = [
            ("Copyright (c) 2023 Example Corp", ("2023", "Example Corp")),
            ("Copyright © 2020-2023 Example Corp", ("2020-2023", "Example Corp")),
            ("copyright (c) 2023 Example Corp", ("2023", "Example Corp")),
            ("Copyright 2023 Example Corp", ("2023", "Example Corp")),
            ("© 2023 Example Corp", ("2023", "Example Corp")),
        ]

        for text, expected_groups in test_cases:
            for pattern in patterns.COPYRIGHT_PATTERNS:
                match = re.search(pattern, text, re.IGNORECASE)
                if match and match.groups() == expected_groups:
                    break
            else:
                pytest.fail(f"No pattern matched: {text}")

    def test_language_comment_styles(self):
        """Test language to comment style mapping."""
        patterns = SPDXPatterns()

        assert patterns.LANGUAGE_COMMENT_STYLES['python'] == 'python_style'
        assert patterns.LANGUAGE_COMMENT_STYLES['javascript'] == 'c_style'
        assert patterns.LANGUAGE_COMMENT_STYLES['c'] == 'c_style'
        assert patterns.LANGUAGE_COMMENT_STYLES['html'] == 'html_style'
        assert patterns.LANGUAGE_COMMENT_STYLES['shell'] == 'shell_style'


class TestSPDXParser:
    """Test SPDX parser functionality."""

    def test_parser_initialization(self):
        """Test parser initialization."""
        parser = SPDXParser()
        assert parser.patterns is not None
        assert parser._compiled_patterns is not None

    def test_parse_file_with_spdx_header(self):
        """Test parsing file with SPDX header."""
        parser = SPDXParser()

        # Create a mock file info with Python content
        content = '''# SPDX-License-Identifier: MIT
# Copyright (c) 2023 Example Corp
# Example Project

print("Hello, world!")
'''

        file_info = Mock()
        file_info.content = content
        file_info.language = "python"

        spdx_info = parser.parse_file(file_info)

        assert spdx_info.license_identifier == "MIT"
        assert spdx_info.copyright_text == "Copyright (c) 2023 Example Corp"
        assert spdx_info.project_attribution == "Example Project"
        assert spdx_info.declaration_type == SPDXDeclarationType.HEADER
        assert spdx_info.raw_declaration is not None

    def test_parse_file_without_spdx(self):
        """Test parsing file without SPDX information."""
        parser = SPDXParser()

        content = '''print("Hello, world!")
# This is just a regular comment
'''

        file_info = Mock()
        file_info.content = content
        file_info.language = "python"

        spdx_info = parser.parse_file(file_info)

        assert spdx_info.license_identifier is None
        assert spdx_info.copyright_text is None
        assert spdx_info.project_attribution is None
        assert spdx_info.declaration_type == SPDXDeclarationType.NONE

    def test_parse_file_with_partial_spdx(self):
        """Test parsing file with partial SPDX information."""
        parser = SPDXParser()

        content = '''# SPDX-License-Identifier: MIT
# Just a regular comment

print("Hello, world!")
'''

        file_info = Mock()
        file_info.content = content
        file_info.language = "python"

        spdx_info = parser.parse_file(file_info)

        assert spdx_info.license_identifier == "MIT"
        assert spdx_info.copyright_text is None
        assert spdx_info.project_attribution is None

    def test_parse_different_languages(self):
        """Test parsing different programming languages."""
        parser = SPDXParser()

        # JavaScript
        js_content = '''// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2023 Example Corp
// Example Project

console.log("Hello, world!");
'''
        js_file = Mock(content=js_content, language="javascript")
        js_spdx = parser.parse_file(js_file)
        assert js_spdx.license_identifier == "Apache-2.0"

        # C/C++
        c_content = '''/* SPDX-License-Identifier: GPL-3.0
 * Copyright (c) 2023 Example Corp
 * Example Project
 */

#include <stdio.h>
'''
        c_file = Mock(content=c_content, language="c")
        c_spdx = parser.parse_file(c_file)
        assert c_spdx.license_identifier == "GPL-3.0"

        # HTML
        html_content = '''<!-- SPDX-License-Identifier: BSD-3-Clause -->
<!-- Copyright (c) 2023 Example Corp -->
<!-- Example Project -->

<html>
<body>
</body>
</html>
'''
        html_file = Mock(content=html_content, language="html")
        html_spdx = parser.parse_file(html_file)
        assert html_spdx.license_identifier == "BSD-3-Clause"

    def test_parse_spdx_version(self):
        """Test parsing SPDX version."""
        parser = SPDXParser()

        content = '''# SPDX-License-Identifier: MIT
# SPDX-Version: SPDX-2.2
# Copyright (c) 2023 Example Corp

print("Hello, world!")
'''

        file_info = Mock()
        file_info.content = content
        file_info.language = "python"

        spdx_info = parser.parse_file(file_info)

        assert spdx_info.license_identifier == "MIT"
        assert spdx_info.spdx_version == "SPDX-2.2"

    def test_parse_additional_tags(self):
        """Test parsing additional SPDX tags."""
        parser = SPDXParser()

        content = '''# SPDX-License-Identifier: MIT
# SPDX-Copyright: Copyright (c) 2023 Example Corp
# SPDX-Contributor: John Doe
# SPDX-Contributor: Jane Smith
# SPDX-DownloadLocation: https://example.com/download
# SPDX-Homepage: https://example.com
# Example Project

print("Hello, world!")
'''

        file_info = Mock()
        file_info.content = content
        file_info.language = "python"

        spdx_info = parser.parse_file(file_info)

        assert spdx_info.license_identifier == "MIT"
        assert "contributors" in spdx_info.additional_tags
        assert "John Doe" in spdx_info.additional_tags["contributors"]
        assert "Jane Smith" in spdx_info.additional_tags["contributors"]
        assert spdx_info.additional_tags["download_location"] == "https://example.com/download"
        assert spdx_info.additional_tags["homepage"] == "https://example.com"

    def test_parse_complex_license_expressions(self):
        """Test parsing complex license expressions."""
        parser = SPDXParser()

        # License with OR
        content_or = '''# SPDX-License-Identifier: MIT OR Apache-2.0
# Copyright (c) 2023 Example Corp
'''
        file_or = Mock(content=content_or, language="python")
        spdx_or = parser.parse_file(file_or)
        assert spdx_or.license_identifier == "MIT OR Apache-2.0"

        # License with AND
        content_and = '''# SPDX-License-Identifier: MIT AND BSD-3-Clause
# Copyright (c) 2023 Example Corp
'''
        file_and = Mock(content=content_and, language="python")
        spdx_and = parser.parse_file(file_and)
        assert spdx_and.license_identifier == "MIT AND BSD-3-Clause"

        # License with WITH exception
        content_with = '''# SPDX-License-Identifier: GPL-3.0 WITH Classpath-exception-2.0
# Copyright (c) 2023 Example Corp
'''
        file_with = Mock(content=content_with, language="python")
        spdx_with = parser.parse_file(file_with)
        assert spdx_with.license_identifier == "GPL-3.0 WITH Classpath-exception-2.0"

    def test_parse_malformed_spdx(self):
        """Test parsing malformed SPDX declarations."""
        parser = SPDXParser()

        # Malformed license identifier
        content = '''# SPDX-License-Identifier:
# Copyright (c) 2023 Example Corp

print("Hello, world!")
'''

        file_info = Mock()
        file_info.content = content
        file_info.language = "python"

        spdx_info = parser.parse_file(file_info)

        # Should still parse but may have validation errors
        assert spdx_info.license_identifier is None or spdx_info.license_identifier.strip() == ""
        assert spdx_info.copyright_text == "Copyright (c) 2023 Example Corp"

    def test_parse_empty_file(self):
        """Test parsing empty file."""
        parser = SPDXParser()

        file_info = Mock()
        file_info.content = ""
        file_info.language = "python"

        spdx_info = parser.parse_file(file_info)

        assert spdx_info.license_identifier is None
        assert spdx_info.copyright_text is None
        assert spdx_info.project_attribution is None
        assert spdx_info.declaration_type == SPDXDeclarationType.NONE

    def test_parse_file_with_shebang(self):
        """Test parsing file with shebang."""
        parser = SPDXParser()

        content = '''#!/usr/bin/env python
# SPDX-License-Identifier: MIT
# Copyright (c) 2023 Example Corp
# Example Project

print("Hello, world!")
'''

        file_info = Mock()
        file_info.content = content
        file_info.language = "python"

        spdx_info = parser.parse_file(file_info)

        assert spdx_info.license_identifier == "MIT"
        assert spdx_info.copyright_text == "Copyright (c) 2023 Example Corp"
        assert spdx_info.project_attribution == "Example Project"

    def test_get_supported_languages(self):
        """Test getting supported languages."""
        parser = SPDXParser()
        languages = parser.get_supported_languages()

        assert "python" in languages
        assert "javascript" in languages
        assert "c" in languages
        assert "cpp" in languages
        assert "html" in languages

    def test_is_language_supported(self):
        """Test language support checking."""
        parser = SPDXParser()

        assert parser.is_language_supported("python") is True
        assert parser.is_language_supported("javascript") is True
        assert parser.is_language_supported("c") is True
        assert parser.is_language_supported("unknown") is False

    def test_parse_error_handling(self):
        """Test error handling during parsing."""
        parser = SPDXParser()

        # Mock file info that will cause an error
        file_info = Mock()
        file_info.content = "some content"
        file_info.language = "python"
        file_info.filepath = "test.py"

        # Mock an exception during parsing
        with patch.object(parser, '_extract_license_header', side_effect=Exception("Test error")):
            spdx_info = parser.parse_file(file_info)

            # Should return SPDXInfo with error
            assert spdx_info.declaration_type == SPDXDeclarationType.NONE
            assert len(spdx_info.validation_errors) > 0
            assert any("Failed to parse SPDX information" in error.message for error in spdx_info.validation_errors)


class TestCreateDefaultParser:
    """Test default parser creation."""

    def test_create_default_parser(self):
        """Test creating default parser."""
        parser = create_default_parser()
        assert isinstance(parser, SPDXParser)
        assert parser.patterns is not None
        assert parser._compiled_patterns is not None