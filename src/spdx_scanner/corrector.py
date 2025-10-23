"""
SPDX corrector component for SPDX Scanner.

This module provides functionality to automatically correct and complete
SPDX license declarations in source code files according to configuration
and templates.
"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
import re

from .models import SPDXInfo, FileInfo, CorrectionResult, ValidationError, ValidationSeverity


logger = logging.getLogger(__name__)


class LicenseHeaderTemplates:
    """Default license header templates for different programming languages."""

    # Templates by language
    TEMPLATES = {
        'python': '''# SPDX-License-Identifier: {license}
# Copyright (c) {year} {copyright_holder}
# {project_name}

''',
        'javascript': '''// SPDX-License-Identifier: {license}
// Copyright (c) {year} {copyright_holder}
// {project_name}

''',
        'typescript': '''// SPDX-License-Identifier: {license}
// Copyright (c) {year} {copyright_holder}
// {project_name}

''',
        'java': '''// SPDX-License-Identifier: {license}
// Copyright (c) {year} {copyright_holder}
// {project_name}

''',
        'c': '''/* SPDX-License-Identifier: {license}
 * Copyright (c) {year} {copyright_holder}
 * {project_name}
 */

''',
        'cpp': '''/* SPDX-License-Identifier: {license}
 * Copyright (c) {year} {copyright_holder}
 * {project_name}
 */

''',
        'go': '''// SPDX-License-Identifier: {license}
// Copyright (c) {year} {copyright_holder}
// {project_name}

''',
        'rust': '''// SPDX-License-Identifier: {license}
// Copyright (c) {year} {copyright_holder}
// {project_name}

''',
        'shell': '''# SPDX-License-Identifier: {license}
# Copyright (c) {year} {copyright_holder}
# {project_name}

''',
        'ruby': '''# SPDX-License-Identifier: {license}
# Copyright (c) {year} {copyright_holder}
# {project_name}

''',
        'html': '''<!-- SPDX-License-Identifier: {license} -->
<!-- Copyright (c) {year} {copyright_holder} -->
<!-- {project_name} -->

''',
        'css': '''/* SPDX-License-Identifier: {license}
 * Copyright (c) {year} {copyright_holder}
 * {project_name}
 */

''',
        'sql': '''-- SPDX-License-Identifier: {license}
-- Copyright (c) {year} {copyright_holder}
-- {project_name}

''',
        'default': '''SPDX-License-Identifier: {license}
Copyright (c) {year} {copyright_holder}
{project_name}

''',
    }

    # Language-specific comment styles for inline corrections
    COMMENT_STYLES = {
        'python': {'start': '# ', 'end': '', 'prefix': '# '},
        'javascript': {'start': '// ', 'end': '', 'prefix': '// '},
        'typescript': {'start': '// ', 'end': '', 'prefix': '// '},
        'java': {'start': '// ', 'end': '', 'prefix': '// '},
        'c': {'start': '/* ', 'end': ' */', 'prefix': ' * '},
        'cpp': {'start': '/* ', 'end': ' */', 'prefix': ' * '},
        'go': {'start': '// ', 'end': '', 'prefix': '// '},
        'rust': {'start': '// ', 'end': '', 'prefix': '// '},
        'shell': {'start': '# ', 'end': '', 'prefix': '# '},
        'ruby': {'start': '# ', 'end': '', 'prefix': '# '},
        'html': {'start': '<!-- ', 'end': ' -->', 'prefix': '<!-- '},
        'css': {'start': '/* ', 'end': ' */', 'prefix': ' * '},
        'sql': {'start': '-- ', 'end': '', 'prefix': '-- '},
        'default': {'start': '', 'end': '', 'prefix': ''},
    }

    @classmethod
    def get_template(cls, language: str) -> str:
        """Get template for a specific language."""
        return cls.TEMPLATES.get(language, cls.TEMPLATES['default'])

    @classmethod
    def get_comment_style(cls, language: str) -> Dict[str, str]:
        """Get comment style for a specific language."""
        return cls.COMMENT_STYLES.get(language, cls.COMMENT_STYLES['default'])


class SPDXCorrector:
    """SPDX license header corrector."""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        templates: Optional[Dict[str, str]] = None,
    ):
        """Initialize the corrector with configuration and templates."""
        self.config = config or {}
        self.templates = templates or LicenseHeaderTemplates.TEMPLATES
        self.create_backups = self.config.get('create_backups', True)
        self.backup_suffix = self.config.get('backup_suffix', '.spdx-backup')
        self.preserve_existing = self.config.get('preserve_existing', True)
        self.default_license = self.config.get('default_license', 'MIT')
        self.default_copyright_holder = self.config.get('default_copyright_holder', 'Unknown')
        self.default_project_name = self.config.get('default_project_name', 'Unknown Project')

    def correct_file(self, file_info: FileInfo, dry_run: bool = False) -> CorrectionResult:
        """Correct SPDX information in a file."""
        start_time = datetime.now()
        result = CorrectionResult(
            original_content=file_info.content,
            corrected_content=file_info.content,
            success=False
        )

        try:
            # Check if file needs correction
            if not file_info.needs_spdx_correction():
                result.success = True
                result.add_change("No SPDX correction needed")
                return result

            # Generate corrected content
            corrected_content = self._generate_corrected_content(file_info)

            if corrected_content == file_info.content:
                result.success = True
                result.add_change("No changes needed")
                return result

            # Apply correction
            if not dry_run:
                # Create backup if requested
                if self.create_backups:
                    backup_path = self._create_backup(file_info.filepath)
                    result.backup_created = True
                    result.backup_path = backup_path

                # Write corrected content
                self._write_corrected_file(file_info.filepath, corrected_content, file_info.encoding)
                result.success = True
                result.add_change("SPDX license header corrected")
            else:
                # Dry run - just show what would be changed
                result.success = True
                result.add_change("SPDX license header would be corrected (dry run)")

            result.corrected_content = corrected_content

            # Calculate correction time
            end_time = datetime.now()
            result.correction_time = (end_time - start_time).total_seconds()

            return result

        except Exception as e:
            logger.error(f"Correction failed for {file_info.filepath}: {e}")
            result.success = False
            result.error_message = str(e)
            return result

    def _generate_corrected_content(self, file_info: FileInfo) -> str:
        """Generate corrected file content with proper SPDX header."""
        original_content = file_info.content
        lines = original_content.split('\n')

        # Determine where to insert the license header
        insert_position = self._find_insert_position(lines, file_info)

        # Generate license header
        license_header = self._generate_license_header(file_info)

        # Insert or replace license header
        if file_info.has_spdx_declaration():
            # Replace existing header
            corrected_lines = self._replace_existing_header(lines, file_info, license_header)
        else:
            # Insert new header
            corrected_lines = (
                lines[:insert_position] +
                license_header.split('\n') +
                lines[insert_position:]
            )

        return '\n'.join(corrected_lines)

    def _find_insert_position(self, lines: List[str], file_info: FileInfo) -> int:
        """Find the position where license header should be inserted."""
        # Skip shebang line if present
        if file_info.has_shebang and lines:
            if lines[0].strip().startswith('#!'):
                return 1

        # Skip empty lines at the beginning
        for i, line in enumerate(lines):
            if line.strip():
                return i

        return 0

    def _generate_license_header(self, file_info: FileInfo) -> str:
        """Generate appropriate license header for the file."""
        # Get template for language
        template = self._get_template_for_language(file_info.language)

        # Get or generate SPDX information
        if file_info.spdx_info and file_info.spdx_info.license_identifier:
            license_id = file_info.spdx_info.license_identifier
            copyright_text = file_info.spdx_info.copyright_text or self._generate_default_copyright()
            project_name = file_info.spdx_info.project_attribution or self.default_project_name
        else:
            license_id = self.default_license
            copyright_text = self._generate_default_copyright()
            project_name = self.default_project_name

        # Extract copyright year and holder
        year, copyright_holder = self._parse_copyright_text(copyright_text)

        # Format template
        header = template.format(
            license=license_id,
            year=year,
            copyright_holder=copyright_holder,
            project_name=project_name,
        )

        return header

    def _get_template_for_language(self, language: str) -> str:
        """Get license header template for a specific language."""
        # Check for custom templates first
        if language in self.templates:
            return self.templates[language]

        # Fall back to default templates
        return LicenseHeaderTemplates.get_template(language)

    def _generate_default_copyright(self) -> str:
        """Generate default copyright text."""
        current_year = datetime.now().year
        return f"Copyright (c) {current_year} {self.default_copyright_holder}"

    def _parse_copyright_text(self, copyright_text: Optional[str]) -> tuple[str, str]:
        """Parse copyright text to extract year and holder."""
        if not copyright_text:
            current_year = datetime.now().year
            return str(current_year), self.default_copyright_holder

        # Extract year
        year_pattern = r'\b(19|20)\d{2}\b'
        year_match = re.search(year_pattern, copyright_text)
        if year_match:
            year = year_match.group(0)
        else:
            year = str(datetime.now().year)

        # Extract holder (everything after the year)
        holder_pattern = r'\b(19|20)\d{2}\s+(.+)$'
        holder_match = re.search(holder_pattern, copyright_text)
        if holder_match:
            holder = holder_match.group(2).strip()
        else:
            holder = self.default_copyright_holder

        return year, holder

    def _replace_existing_header(self, lines: List[str], file_info: FileInfo, new_header: str) -> List[str]:
        """Replace existing SPDX header with new one."""
        # Find existing header boundaries
        header_start, header_end = self._find_header_boundaries(lines, file_info)

        if header_start is None or header_end is None:
            # Could not find existing header, insert at beginning
            return [new_header.rstrip()] + lines

        # Replace header
        new_lines = lines[:header_start]
        new_lines.extend(new_header.rstrip().split('\n'))
        new_lines.extend(lines[header_end + 1:])

        return new_lines

    def _find_header_boundaries(self, lines: List[str], file_info: FileInfo) -> tuple[Optional[int], Optional[int]]:
        """Find the start and end lines of the existing SPDX header."""
        if not file_info.spdx_info or not file_info.spdx_info.raw_declaration:
            return None, None

        # Find lines containing SPDX information
        spdx_lines = []
        for i, line in enumerate(lines):
            if self._contains_spdx_info(line):
                spdx_lines.append(i)

        if not spdx_lines:
            return None, None

        # Find header boundaries around SPDX lines
        header_start = min(spdx_lines)
        header_end = max(spdx_lines)

        # Expand to include comment boundaries
        comment_style = LicenseHeaderTemplates.get_comment_style(file_info.language)
        prefix = comment_style['prefix']

        # Find start of comment block
        while header_start > 0:
            prev_line = lines[header_start - 1].strip()
            if not prev_line or prev_line.startswith(prefix.strip()) or self._is_comment_line(prev_line, file_info.language):
                header_start -= 1
            else:
                break

        # Find end of comment block
        while header_end < len(lines) - 1:
            next_line = lines[header_end + 1].strip()
            if not next_line or next_line.startswith(prefix.strip()) or self._is_comment_line(next_line, file_info.language):
                header_end += 1
            else:
                break

        return header_start, header_end

    def _contains_spdx_info(self, line: str) -> bool:
        """Check if line contains SPDX information."""
        line_upper = line.upper()
        return (
            'SPDX-LICENSE-IDENTIFIER' in line_upper or
            'SPDX-COPYRIGHT' in line_upper or
            'SPDX-VERSION' in line_upper or
            'SPDX-PROJECT' in line_upper
        )

    def _is_comment_line(self, line: str, language: str) -> bool:
        """Check if line is a comment line for the given language."""
        line_stripped = line.strip()
        comment_style = LicenseHeaderTemplates.get_comment_style(language)

        if comment_style['prefix']:
            return line_stripped.startswith(comment_style['prefix'].strip())

        # Default comment detection
        return (
            line_stripped.startswith('//') or
            line_stripped.startswith('#') or
            line_stripped.startswith('/*') or
            line_stripped.startswith('*/') or
            line_stripped.startswith('*')
        )

    def _create_backup(self, filepath: Path) -> Path:
        """Create a backup of the original file."""
        backup_path = filepath.with_suffix(filepath.suffix + self.backup_suffix)
        shutil.copy2(filepath, backup_path)
        logger.info(f"Created backup: {backup_path}")
        return backup_path

    def _write_corrected_file(self, filepath: Path, content: str, encoding: str) -> None:
        """Write corrected content to file."""
        with open(filepath, 'w', encoding=encoding) as f:
            f.write(content)
        logger.info(f"Wrote corrected file: {filepath}")

    def validate_correction(self, file_info: FileInfo) -> List[ValidationError]:
        """Validate that a correction can be safely applied."""
        errors = []

        # Check if file is too large
        if file_info.size > 10 * 1024 * 1024:  # 10MB
            errors.append(ValidationError(
                severity=ValidationSeverity.WARNING,
                message="File is very large (>10MB), correction may be slow",
                rule_id="large_file_warning"
            ))

        # Check if file is binary
        if file_info.is_binary:
            errors.append(ValidationError(
                severity=ValidationSeverity.ERROR,
                message="Cannot correct binary files",
                rule_id="binary_file_error"
            ))

        # Check if file is empty
        if file_info.is_empty:
            errors.append(ValidationError(
                severity=ValidationSeverity.WARNING,
                message="File is empty, correction will add only license header",
                rule_id="empty_file_warning"
            ))

        # Check if backup directory is writable
        if self.create_backups:
            backup_path = file_info.filepath.with_suffix(file_info.filepath.suffix + self.backup_suffix)
            try:
                # Test if we can write to the backup location
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                with open(backup_path, 'w') as f:
                    f.write("")
                backup_path.unlink()  # Remove test file
            except (OSError, PermissionError) as e:
                errors.append(ValidationError(
                    severity=ValidationSeverity.ERROR,
                    message=f"Cannot create backup file: {e}",
                    rule_id="backup_permission_error"
                ))

        return errors

    def get_available_templates(self) -> List[str]:
        """Get list of available license header templates."""
        return list(self.templates.keys())

    def add_custom_template(self, language: str, template: str) -> None:
        """Add a custom template for a specific language."""
        self.templates[language] = template


def create_default_corrector(config: Optional[Dict[str, Any]] = None) -> SPDXCorrector:
    """Create a default SPDX corrector instance."""
    return SPDXCorrector(config)