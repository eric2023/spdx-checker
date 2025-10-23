"""
Tests for SPDX Scanner corrector component.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from spdx_scanner.corrector import SPDXCorrector, LicenseHeaderTemplates, create_default_corrector
from spdx_scanner.models import FileInfo, SPDXInfo, SPDXDeclarationType


class TestLicenseHeaderTemplates:
    """Test license header templates."""

    def test_get_template_python(self):
        """Test getting Python template."""
        template = LicenseHeaderTemplates.get_template("python")
        assert "SPDX-License-Identifier: {license}" in template
        assert "# " in template  # Python comment style
        assert "{copyright_holder}" in template
        assert "{project_name}" in template

    def test_get_template_javascript(self):
        """Test getting JavaScript template."""
        template = LicenseHeaderTemplates.get_template("javascript")
        assert "SPDX-License-Identifier: {license}" in template
        assert "// " in template  # JavaScript comment style
        assert "{copyright_holder}" in template
        assert "{project_name}" in template

    def test_get_template_c(self):
        """Test getting C template."""
        template = LicenseHeaderTemplates.get_template("c")
        assert "SPDX-License-Identifier: {license}" in template
        assert "/* " in template  # C comment style
        assert " * " in template  # C comment continuation
        assert "{copyright_holder}" in template
        assert "{project_name}" in template

    def test_get_template_default(self):
        """Test getting default template."""
        template = LicenseHeaderTemplates.get_template("unknown")
        default_template = LicenseHeaderTemplates.get_template("default")
        assert template == default_template

    def test_get_comment_style_python(self):
        """Test getting Python comment style."""
        style = LicenseHeaderTemplates.get_comment_style("python")
        assert style["start"] == "# "
        assert style["end"] == ""
        assert style["prefix"] == "# "

    def test_get_comment_style_c(self):
        """Test getting C comment style."""
        style = LicenseHeaderTemplates.get_comment_style("c")
        assert style["start"] == "/* "
        assert style["end"] == " */"
        assert style["prefix"] == " * "

    def test_get_comment_style_default(self):
        """Test getting default comment style."""
        style = LicenseHeaderTemplates.get_comment_style("unknown")
        default_style = LicenseHeaderTemplates.get_comment_style("default")
        assert style == default_style


class TestSPDXCorrector:
    """Test SPDX corrector functionality."""

    def test_corrector_initialization(self):
        """Test corrector initialization."""
        config = {
            'create_backups': False,
            'backup_suffix': '.custom-backup',
            'preserve_existing': False,
            'default_license': 'Apache-2.0',
            'default_copyright_holder': 'Test Corp',
            'default_project_name': 'Test Project',
        }

        corrector = SPDXCorrector(config)

        assert corrector.create_backups is False
        assert corrector.backup_suffix == '.custom-backup'
        assert corrector.preserve_existing is False
        assert corrector.default_license == 'Apache-2.0'
        assert corrector.default_copyright_holder == 'Test Corp'
        assert corrector.default_project_name == 'Test Project'

    def test_corrector_initialization_defaults(self):
        """Test corrector initialization with defaults."""
        corrector = SPDXCorrector()

        assert corrector.create_backups is True
        assert corrector.backup_suffix == '.spdx-backup'
        assert corrector.preserve_existing is True
        assert corrector.default_license == 'MIT'
        assert corrector.default_copyright_holder == 'Unknown'
        assert corrector.default_project_name == 'Unknown Project'

    def test_correct_file_no_changes_needed(self):
        """Test correcting file that doesn't need changes."""
        corrector = SPDXCorrector()

        # Create file info with valid SPDX
        spdx_info = SPDXInfo(
            license_identifier="MIT",
            copyright_text="Copyright (c) 2023 Example Corp",
            project_attribution="Example Project"
        )

        file_info = FileInfo(
            filepath=Path("test.py"),
            language="python",
            content="# SPDX-License-Identifier: MIT\n# Copyright (c) 2023 Example Corp\n# Example Project\n\nprint('hello')",
            spdx_info=spdx_info
        )

        result = corrector.correct_file(file_info, dry_run=True)

        assert result.success is True
        assert result.has_changes() is False
        assert "No SPDX correction needed" in result.changes_made
        assert result.original_content == result.corrected_content

    def test_correct_file_missing_spdx(self):
        """Test correcting file missing SPDX information."""
        corrector = SPDXCorrector()

        # Create file info without SPDX
        file_info = FileInfo(
            filepath=Path("test.py"),
            language="python",
            content="print('hello')",
            spdx_info=SPDXInfo()  # Empty SPDX info
        )

        result = corrector.correct_file(file_info, dry_run=True)

        assert result.success is True
        assert result.has_changes() is True
        assert "SPDX license header would be corrected" in result.changes_made[0]
        assert result.original_content != result.corrected_content

        # Check that license header was added
        assert "SPDX-License-Identifier: MIT" in result.corrected_content
        assert "Copyright (c)" in result.corrected_content
        assert "Unknown" in result.corrected_content  # Default copyright holder

    def test_correct_file_different_languages(self):
        """Test correcting files in different programming languages."""
        corrector = SPDXCorrector()

        languages_and_content = [
            ("python", "print('hello')"),
            ("javascript", "console.log('hello');"),
            ("c", '#include <stdio.h>\nint main() { return 0; }'),
            ("html", "<html><body>Hello</body></html>"),
        ]

        for language, content in languages_and_content:
            file_info = FileInfo(
                filepath=Path(f"test.{language}"),
                language=language,
                content=content,
                spdx_info=SPDXInfo()  # Empty SPDX info
            )

            result = corrector.correct_file(file_info, dry_run=True)

            assert result.success is True
            assert result.has_changes() is True
            assert "SPDX-License-Identifier: MIT" in result.corrected_content

            # Check language-specific comment style
            if language == "python":
                assert result.corrected_content.startswith("# SPDX-License-Identifier: MIT")
            elif language == "javascript":
                assert result.corrected_content.startswith("// SPDX-License-Identifier: MIT")
            elif language == "c":
                assert "/* SPDX-License-Identifier: MIT" in result.corrected_content
            elif language == "html":
                assert result.corrected_content.startswith("<!-- SPDX-License-Identifier: MIT")

    def test_correct_file_with_shebang(self):
        """Test correcting file with shebang."""
        corrector = SPDXCorrector()

        file_info = FileInfo(
            filepath=Path("test.py"),
            language="python",
            content="#!/usr/bin/env python\nprint('hello')",
            has_shebang=True,
            spdx_info=SPDXInfo()  # Empty SPDX info
        )

        result = corrector.correct_file(file_info, dry_run=True)

        assert result.success is True
        assert result.has_changes() is True

        # Check that license header is added after shebang
        lines = result.corrected_content.split('\n')
        assert lines[0] == "#!/usr/bin/env python"
        assert "SPDX-License-Identifier: MIT" in lines[1]

    def test_correct_file_with_existing_spdx(self):
        """Test correcting file with existing but incomplete SPDX."""
        corrector = SPDXCorrector()

        # File with only license identifier
        file_info = FileInfo(
            filepath=Path("test.py"),
            language="python",
            content="# SPDX-License-Identifier: MIT\n\nprint('hello')",
            spdx_info=SPDXInfo(license_identifier="MIT")  # Only license, no copyright
        )

        result = corrector.correct_file(file_info, dry_run=True)

        assert result.success is True
        assert result.has_changes() is True

        # Should add copyright information
        assert "Copyright (c)" in result.corrected_content

    def test_correct_file_backup_creation(self):
        """Test backup file creation during correction."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "test.py"
            test_file.write_text("print('hello')")

            corrector = SPDXCorrector()

            file_info = FileInfo(
                filepath=test_file,
                language="python",
                content="print('hello')",
                spdx_info=SPDXInfo()  # Empty SPDX info
            )

            result = corrector.correct_file(file_info, dry_run=False)

            assert result.success is True
            assert result.backup_created is True
            assert result.backup_path is not None
            assert result.backup_path.exists()

            # Check backup content
            backup_content = result.backup_path.read_text()
            assert backup_content == "print('hello')"

    def test_correct_file_no_backup(self):
        """Test correction without backup creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "test.py"
            test_file.write_text("print('hello')")

            corrector = SPDXCorrector({'create_backups': False})

            file_info = FileInfo(
                filepath=test_file,
                language="python",
                content="print('hello')",
                spdx_info=SPDXInfo()  # Empty SPDX info
            )

            result = corrector.correct_file(file_info, dry_run=False)

            assert result.success is True
            assert result.backup_created is False
            assert result.backup_path is None

    def test_correct_file_dry_run(self):
        """Test dry run mode."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "test.py"
            original_content = "print('hello')"
            test_file.write_text(original_content)

            corrector = SPDXCorrector()

            file_info = FileInfo(
                filepath=test_file,
                language="python",
                content=original_content,
                spdx_info=SPDXInfo()  # Empty SPDX info
            )

            result = corrector.correct_file(file_info, dry_run=True)

            assert result.success is True
            assert result.has_changes() is True
            assert "dry run" in result.changes_made[0]

            # File should not be modified in dry run
            assert test_file.read_text() == original_content

    def test_correct_file_error_handling(self):
        """Test error handling during correction."""
        corrector = SPDXCorrector()

        # Mock file info that will cause an error
        file_info = Mock()
        file_info.filepath = Path("test.py")
        file_info.language = "python"
        file_info.content = "print('hello')"
        file_info.needs_spdx_correction.return_value = True
        file_info.spdx_info = SPDXInfo()

        # Mock _generate_corrected_content to raise an exception
        with patch.object(corrector, '_generate_corrected_content', side_effect=Exception("Test error")):
            result = corrector.correct_file(file_info, dry_run=True)

            assert result.success is False
            assert result.error_message == "Test error"
            assert len(result.changes_made) == 0

    def test_validate_correction_binary_file(self):
        """Test validation for binary files."""
        corrector = SPDXCorrector()

        file_info = FileInfo(
            filepath=Path("test.bin"),
            language="unknown",
            content="binary content",
            is_binary=True,
            spdx_info=SPDXInfo()  # Empty SPDX info
        )

        errors = corrector.validate_correction(file_info)

        assert len(errors) >= 1
        assert any("Cannot correct binary files" in error.message for error in errors)

    def test_validate_correction_large_file(self):
        """Test validation for large files."""
        corrector = SPDXCorrector()

        file_info = FileInfo(
            filepath=Path("test.py"),
            language="python",
            content="x" * 1000,
            size=15 * 1024 * 1024,  # 15MB
            spdx_info=SPDXInfo()  # Empty SPDX info
        )

        errors = corrector.validate_correction(file_info)

        assert len(errors) >= 1
        assert any("File is very large" in error.message for error in errors)

    def test_get_available_templates(self):
        """Test getting available templates."""
        corrector = SPDXCorrector()

        templates = corrector.get_available_templates()
        assert "python" in templates
        assert "javascript" in templates
        assert "c" in templates
        assert "html" in templates

    def test_add_custom_template(self):
        """Test adding custom template."""
        corrector = SPDXCorrector()

        custom_template = "# Custom SPDX Header\n# License: {license}\n# Copyright: {copyright_holder}\n"
        corrector.add_custom_template("custom", custom_template)

        assert "custom" in corrector.templates
        assert corrector.templates["custom"] == custom_template


class TestCreateDefaultCorrector:
    """Test default corrector creation."""

    def test_create_default_corrector(self):
        """Test creating default corrector."""
        corrector = create_default_corrector()
        assert isinstance(corrector, SPDXCorrector)
        assert corrector.config == {}

    def test_create_default_corrector_with_config(self):
        """Test creating default corrector with configuration."""
        config = {'default_license': 'GPL-3.0'}
        corrector = create_default_corrector(config)
        assert isinstance(corrector, SPDXCorrector)
        assert corrector.default_license == 'GPL-3.0'