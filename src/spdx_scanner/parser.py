"""
SPDX parser component for SPDX Scanner.

This module provides functionality to parse and extract SPDX license declarations
from source code files, supporting various comment styles and formats.
"""

import re
from typing import Optional, Dict, List, Tuple, Any
from pathlib import Path
import logging

from .models import SPDXInfo, SPDXDeclarationType, ValidationError, ValidationSeverity


logger = logging.getLogger(__name__)


class SPDXPatterns:
    """SPDX license declaration patterns for different languages and formats."""

    # SPDX license identifier patterns
    LICENSE_IDENTIFIER_PATTERNS = [
        r'SPDX-License-Identifier:\s*([A-Za-z0-9\-\+\.\(\)\s]+)',
        r'spdx-license-identifier:\s*([A-Za-z0-9\-\+\.\(\)\s]+)',
        r'SPDX-License-Identifier\s*:\s*([A-Za-z0-9\-\+\.\(\)\s]+)',
    ]

    # Copyright patterns
    COPYRIGHT_PATTERNS = [
        r'Copyright\s*\(c\)\s*([0-9\-\,\s]+)\s+(.+)',
        r'Copyright\s*©\s*([0-9\-\,\s]+)\s+(.+)',
        r'copyright\s*\(c\)\s*([0-9\-\,\s]+)\s+(.+)',
        r'Copyright\s+([0-9\-\,\s]+)\s+(.+)',
        r'©\s*([0-9\-\,\s]+)\s+(.+)',
    ]

    # Project attribution patterns
    PROJECT_PATTERNS = [
        r'([A-Za-z0-9\s\-_\.]+)\s+Project',
        r'Project:\s*([A-Za-z0-9\s\-_\.]+)',
        r'project:\s*([A-Za-z0-9\s\-_\.]+)',
        r'([A-Za-z0-9\s\-_\.]+)\s+Licensed',
    ]

    # SPDX version patterns
    SPDX_VERSION_PATTERNS = [
        r'SPDX-Version:\s*([A-Za-z0-9\.\-]+)',
        r'spdx-version:\s*([A-Za-z0-9\.\-]+)',
    ]

    # Comment style patterns by language
    COMMENT_PATTERNS = {
        # C-style comments (C, C++, Java, JavaScript, TypeScript, Go, Rust, etc.)
        'c_style': {
            'single_line': r'^\s*//\s*(.*?)$',
            'multi_line_start': r'^\s*/\*\s*(.*?)$',
            'multi_line_end': r'^(.*?)\s*\*/\s*$',
            'multi_line_content': r'^\s*\*\s*(.*?)$',
        },
        # Python-style comments
        'python_style': {
            'single_line': r'^\s*#\s*(.*?)$',
            'multi_line_start': r'^\s*"""\s*(.*?)$',
            'multi_line_end': r'^(.*?)"""\s*$',
            'multi_line_content': r'^(.*?)$',
        },
        # Shell-style comments
        'shell_style': {
            'single_line': r'^\s*#\s*(.*?)$',
        },
        # HTML/XML-style comments
        'html_style': {
            'multi_line_start': r'^\s*<!--\s*(.*?)$',
            'multi_line_end': r'^(.*?)-->\s*$',
            'multi_line_content': r'^(.*?)-->$',
        },
        # SQL-style comments
        'sql_style': {
            'single_line': r'^\s*--\s*(.*?)$',
            'multi_line_start': r'^\s*/\*\s*(.*?)$',
            'multi_line_end': r'^(.*?)\s*\*/\s*$',
        },
    }

    # Language to comment style mapping
    LANGUAGE_COMMENT_STYLES = {
        'c': 'c_style',
        'cpp': 'c_style',
        'java': 'c_style',
        'javascript': 'c_style',
        'typescript': 'c_style',
        'go': 'c_style',
        'rust': 'c_style',
        'swift': 'c_style',
        'kotlin': 'c_style',
        'php': 'c_style',
        'python': 'python_style',
        'shell': 'shell_style',
        'ruby': 'shell_style',
        'perl': 'shell_style',
        'r': 'shell_style',
        'html': 'html_style',
        'xml': 'html_style',
        'css': 'c_style',
        'scss': 'c_style',
        'sass': 'shell_style',
        'sql': 'sql_style',
    }


class SPDXParser:
    """Parser for SPDX license declarations in source code files."""

    def __init__(self):
        """Initialize the SPDX parser."""
        self.patterns = SPDXPatterns()
        self._compiled_patterns = self._compile_patterns()

    def _compile_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Compile regex patterns for performance."""
        compiled = {}

        # Compile license identifier patterns
        compiled['license_id'] = [re.compile(pattern, re.IGNORECASE) for pattern in self.patterns.LICENSE_IDENTIFIER_PATTERNS]

        # Compile copyright patterns
        compiled['copyright'] = [re.compile(pattern, re.IGNORECASE) for pattern in self.patterns.COPYRIGHT_PATTERNS]

        # Compile project patterns
        compiled['project'] = [re.compile(pattern, re.IGNORECASE) for pattern in self.patterns.PROJECT_PATTERNS]

        # Compile SPDX version patterns
        compiled['spdx_version'] = [re.compile(pattern, re.IGNORECASE) for pattern in self.patterns.SPDX_VERSION_PATTERNS]

        # Compile comment patterns
        compiled['comments'] = {}
        for style, patterns in self.patterns.COMMENT_PATTERNS.items():
            compiled['comments'][style] = {}
            for pattern_type, pattern in patterns.items():
                compiled['comments'][style][pattern_type] = re.compile(pattern, re.IGNORECASE)

        return compiled

    def parse_file(self, file_info) -> SPDXInfo:
        """Parse SPDX information from a FileInfo object."""
        if not file_info.content:
            return SPDXInfo(declaration_type=SPDXDeclarationType.NONE)

        try:
            # Determine comment style based on language
            comment_style = self._get_comment_style(file_info.language)

            # Extract license header
            license_header = self._extract_license_header(file_info.content, comment_style)

            if not license_header:
                return SPDXInfo(declaration_type=SPDXDeclarationType.NONE)

            # Check if header contains any SPDX declarations
            if not self._contains_spdx_declaration(license_header):
                return SPDXInfo(declaration_type=SPDXDeclarationType.NONE)

            # Parse SPDX information from header
            spdx_info = self._parse_spdx_from_header(license_header, comment_style)
            spdx_info.declaration_type = SPDXDeclarationType.HEADER

            # Validate parsed information
            self._validate_parsed_info(spdx_info)

            return spdx_info

        except Exception as e:
            logger.error(f"Error parsing SPDX info from {file_info.filepath}: {e}")
            error = ValidationError(
                severity=ValidationSeverity.ERROR,
                message=f"Failed to parse SPDX information: {str(e)}",
                rule_id="parse_error",
            )
            return SPDXInfo(
                declaration_type=SPDXDeclarationType.NONE,
                validation_errors=[error]
            )

    def _get_comment_style(self, language: str) -> str:
        """Get comment style for a programming language."""
        return self.patterns.LANGUAGE_COMMENT_STYLES.get(language, 'c_style')

    def _extract_license_header(self, content: str, comment_style: str) -> Optional[str]:
        """Extract license header from file content."""
        lines = content.split('\n')
        header_lines = []
        in_header = False
        in_multiline_comment = False

        comment_patterns = self._compiled_patterns['comments'].get(comment_style, {})

        for i, line in enumerate(lines):
            line_stripped = line.strip()

            # Skip empty lines at the beginning
            if not header_lines and not line_stripped:
                continue

            # Check for shebang line
            if i == 0 and line_stripped.startswith('#!'):
                continue

            # Check for SPDX declarations anywhere in the file
            if self._contains_spdx_declaration(line):
                # Look for license header around SPDX declarations
                start_line = max(0, i - 10)  # Look up to 10 lines before
                end_line = min(len(lines), i + 5)  # Look up to 5 lines after

                for j in range(start_line, end_line):
                    if j < len(lines):
                        header_lines.append(lines[j])

                # 继续处理，不要在这里返回，以便收集所有SPDX声明
                continue

            # Traditional header detection based on comment style
            if comment_style == 'c_style':
                result = self._process_c_style_line(line, in_multiline_comment)
                if result['is_comment']:
                    header_lines.append(line)
                    in_multiline_comment = result['in_multiline']
                elif result['is_comment'] is False and header_lines:
                    break

            elif comment_style == 'python_style':
                result = self._process_python_style_line(line, in_multiline_comment)
                if result['is_comment']:
                    header_lines.append(line)
                    in_multiline_comment = result['in_multiline']
                elif result['is_comment'] is False and header_lines:
                    break

            elif comment_style == 'shell_style':
                if line_stripped.startswith('#'):
                    header_lines.append(line)
                elif header_lines and line_stripped:
                    break

            elif comment_style == 'html_style':
                result = self._process_html_style_line(line, in_multiline_comment)
                if result['is_comment']:
                    header_lines.append(line)
                    in_multiline_comment = result['in_multiline']
                elif result['is_comment'] is False and header_lines:
                    # 只有在不是多行注释状态时才停止
                    if not in_multiline_comment:
                        break

            # Stop at first non-empty, non-comment line
            if not in_multiline_comment and header_lines and line_stripped and not self._is_comment_line(line, comment_style):
                break

            # Limit header size to prevent excessive processing
            if len(header_lines) > 50:
                break

        return '\n'.join(header_lines) if header_lines else None

    def _process_c_style_line(self, line: str, in_multiline: bool) -> Dict[str, Any]:
        """Process a C-style comment line."""
        line_stripped = line.strip()

        if in_multiline:
            if '*/' in line:
                return {'is_comment': True, 'in_multiline': False}
            else:
                return {'is_comment': True, 'in_multiline': True}

        if line_stripped.startswith('//'):
            return {'is_comment': True, 'in_multiline': False}

        if line_stripped.startswith('/*'):
            if '*/' in line:
                return {'is_comment': True, 'in_multiline': False}
            else:
                return {'is_comment': True, 'in_multiline': True}

        return {'is_comment': False, 'in_multiline': False}

    def _process_python_style_line(self, line: str, in_multiline: bool) -> Dict[str, Any]:
        """Process a Python-style comment line."""
        line_stripped = line.strip()

        if in_multiline:
            if '"""' in line or "'''" in line:
                return {'is_comment': True, 'in_multiline': False}
            else:
                return {'is_comment': True, 'in_multiline': True}

        if line_stripped.startswith('#'):
            return {'is_comment': True, 'in_multiline': False}

        if line_stripped.startswith('"""') or line_stripped.startswith("'''"):
            if line_stripped.count('"""') == 2 or line_stripped.count("'''") == 2:
                return {'is_comment': True, 'in_multiline': False}
            else:
                return {'is_comment': True, 'in_multiline': True}

        return {'is_comment': False, 'in_multiline': False}

    def _process_html_style_line(self, line: str, in_multiline: bool) -> Dict[str, Any]:
        """Process an HTML-style comment line."""
        line_stripped = line.strip()

        if in_multiline:
            if '-->' in line:
                return {'is_comment': True, 'in_multiline': False}
            else:
                return {'is_comment': True, 'in_multiline': True}

        # 处理单行HTML注释
        if line_stripped.startswith('<!--') and line_stripped.endswith('-->'):
            return {'is_comment': True, 'in_multiline': False}
        elif line_stripped.startswith('<!--'):
            if '-->' in line:
                return {'is_comment': True, 'in_multiline': False}
            else:
                return {'is_comment': True, 'in_multiline': True}

        return {'is_comment': False, 'in_multiline': False}

    def _is_comment_line(self, line: str, comment_style: str) -> bool:
        """Check if a line is a comment line."""
        line_stripped = line.strip()

        if comment_style in ['c_style', 'python_style', 'shell_style']:
            return (
                line_stripped.startswith('//') or
                line_stripped.startswith('#') or
                line_stripped.startswith('/*') or
                line_stripped.startswith('*/') or
                line_stripped.startswith('*')
            )
        elif comment_style == 'html_style':
            return (
                line_stripped.startswith('<!--') or
                line_stripped.endswith('-->') or
                line_stripped.startswith('#')
            )

        return False

    def _contains_spdx_declaration(self, line: str) -> bool:
        """Check if line contains SPDX declaration."""
        line_upper = line.upper()
        return (
            'SPDX-LICENSE-IDENTIFIER:' in line_upper or
            'SPDX-COPYRIGHT:' in line_upper or
            'SPDX-VERSION:' in line_upper or
            'SPDX-PROJECT:' in line_upper or
            'SPDX-CONTRIBUTOR:' in line_upper or
            'SPDX-DOWNLOADLOCATION:' in line_upper or
            'SPDX-HOMEPAGE:' in line_upper
        )

    def _parse_spdx_from_header(self, header: str, comment_style: str) -> SPDXInfo:
        """Parse SPDX information from license header."""
        spdx_info = SPDXInfo()
        spdx_info.raw_declaration = header

        # Extract license identifier
        license_id = self._extract_license_identifier(header)
        if license_id:
            spdx_info.license_identifier = license_id

        # Extract copyright information
        copyright_text = self._extract_copyright(header)
        if copyright_text:
            spdx_info.copyright_text = copyright_text

        # Extract project attribution
        project_attr = self._extract_project_attribution(header)
        if project_attr:
            spdx_info.project_attribution = project_attr

        # Extract SPDX version
        spdx_version = self._extract_spdx_version(header)
        if spdx_version:
            spdx_info.spdx_version = spdx_version

        # Extract additional tags
        additional_tags = self._extract_additional_tags(header)
        if additional_tags:
            spdx_info.additional_tags = additional_tags

        return spdx_info

    def _extract_license_identifier(self, content: str) -> Optional[str]:
        """Extract SPDX license identifier from content."""
        for pattern in self._compiled_patterns['license_id']:
            match = pattern.search(content)
            if match:
                license_id = match.group(1).strip()
                # 清理HTML注释标记
                license_id = license_id.replace('-->', '').strip()
                return license_id
        return None

    def _extract_copyright(self, content: str) -> Optional[str]:
        """Extract copyright information from content."""
        for pattern in self._compiled_patterns['copyright']:
            match = pattern.search(content)
            if match:
                years = match.group(1).strip()
                holder = match.group(2).strip()
                return f"Copyright (c) {years} {holder}"
        return None

    def _extract_project_attribution(self, content: str) -> Optional[str]:
        """Extract project attribution from content."""
        for pattern in self._compiled_patterns['project']:
            match = pattern.search(content)
            if match:
                # 如果模式包含"Project"这个词，返回完整的匹配组
                if 'Project' in pattern.pattern:
                    # 返回匹配组，但包含"Project"这个词
                    start, end = match.span()
                    project_text = content[start:end].strip()
                    return project_text
                else:
                    return match.group(1).strip()
        return None

    def _extract_spdx_version(self, content: str) -> Optional[str]:
        """Extract SPDX version from content."""
        # 首先尝试直接匹配版本模式
        for pattern in self._compiled_patterns['spdx_version']:
            match = pattern.search(content)
            if match:
                return match.group(1).strip()

        # 如果没有显式版本，但有其他SPDX声明，推断版本
        if any(spdx_keyword in content.upper() for spdx_keyword in ['SPDX-LICENSE-IDENTIFIER', 'SPDX-FILETYPE']):
            # 如果存在SPDX-LICENSE-IDENTIFIER，这是SPDX 2.0+的特征
            if 'SPDX-LICENSE-IDENTIFIER' in content.upper():
                return "2.3"  # 默认返回当前推荐的版本

        return None

    def _extract_additional_tags(self, content: str) -> Dict[str, str]:
        """Extract additional SPDX tags from content."""
        additional_tags = {}

        # Extract Contributor information
        contributor_pattern = r'SPDX-Contributor:\s*(.+)'
        contributor_matches = re.findall(contributor_pattern, content, re.IGNORECASE)
        if contributor_matches:
            additional_tags['contributors'] = ', '.join(match.strip() for match in contributor_matches)

        # Extract Download location
        download_pattern = r'SPDX-DownloadLocation:\s*(.+)'
        download_match = re.search(download_pattern, content, re.IGNORECASE)
        if download_match:
            additional_tags['download_location'] = download_match.group(1).strip()

        # Extract Files analyzed
        files_analyzed_pattern = r'SPDX-FilesAnalyzed:\s*(.+)'
        files_analyzed_match = re.search(files_analyzed_pattern, content, re.IGNORECASE)
        if files_analyzed_match:
            additional_tags['files_analyzed'] = files_analyzed_match.group(1).strip()

        # Extract Homepage
        homepage_pattern = r'SPDX-Homepage:\s*(.+)'
        homepage_match = re.search(homepage_pattern, content, re.IGNORECASE)
        if homepage_match:
            additional_tags['homepage'] = homepage_match.group(1).strip()

        return additional_tags

    def _validate_parsed_info(self, spdx_info: SPDXInfo) -> None:
        """Validate the parsed SPDX information."""
        errors = []

        # Validate license identifier
        if spdx_info.license_identifier:
            if not self._is_valid_license_identifier(spdx_info.license_identifier):
                errors.append(ValidationError(
                    severity=ValidationSeverity.ERROR,
                    message=f"Invalid SPDX license identifier: {spdx_info.license_identifier}",
                    rule_id="invalid_license_id",
                    suggestion="Use a valid SPDX license identifier from https://spdx.org/licenses/"
                ))

        # Validate copyright format
        if spdx_info.copyright_text:
            if not self._is_valid_copyright_format(spdx_info.copyright_text):
                errors.append(ValidationError(
                    severity=ValidationSeverity.WARNING,
                    message="Copyright text may not follow standard format",
                    rule_id="copyright_format_warning",
                    suggestion="Use format: 'Copyright (c) [year] [holder]'"
                ))

        # Validate SPDX version
        if spdx_info.spdx_version:
            if not self._is_valid_spdx_version(spdx_info.spdx_version):
                errors.append(ValidationError(
                    severity=ValidationSeverity.WARNING,
                    message=f"Unusual SPDX version: {spdx_info.spdx_version}",
                    rule_id="spdx_version_warning",
                    suggestion="Consider using standard SPDX version format"
                ))

        spdx_info.validation_errors = errors

    def _is_valid_license_identifier(self, license_id: str) -> bool:
        """Check if license identifier follows SPDX format."""
        # Basic SPDX license identifier validation
        # This is a simplified check - in production, you'd validate against
        # the official SPDX license list
        valid_pattern = r'^[A-Za-z0-9\-\+\.\(\)]+$'
        return bool(re.match(valid_pattern, license_id))

    def _is_valid_copyright_format(self, copyright_text: str) -> bool:
        """Check if copyright text follows standard format."""
        standard_pattern = r'^Copyright\s*\(c\)\s*[0-9\-\,\s]+\s+.+$'
        return bool(re.match(standard_pattern, copyright_text, re.IGNORECASE))

    def _is_valid_spdx_version(self, version: str) -> bool:
        """Check if SPDX version follows expected format."""
        version_pattern = r'^SPDX-[0-9]+\.[0-9]+$'
        return bool(re.match(version_pattern, version, re.IGNORECASE))

    def get_supported_languages(self) -> List[str]:
        """Get list of supported programming languages."""
        return list(self.patterns.LANGUAGE_COMMENT_STYLES.keys())

    def is_language_supported(self, language: str) -> bool:
        """Check if a language is supported for SPDX parsing."""
        return language in self.patterns.LANGUAGE_COMMENT_STYLES


def create_default_parser() -> SPDXParser:
    """Create a default SPDX parser instance."""
    return SPDXParser()