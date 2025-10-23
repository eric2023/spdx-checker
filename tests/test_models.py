"""
Tests for SPDX Scanner models.
"""

import pytest
from datetime import datetime
from pathlib import Path

from spdx_scanner.models import (
    SPDXInfo,
    FileInfo,
    ValidationResult,
    ValidationError,
    ValidationSeverity,
    SPDXDeclarationType,
    CorrectionResult,
    ScanResult,
    ScanSummary,
)


class TestSPDXInfo:
    """Test SPDXInfo model."""

    def test_spdx_info_creation(self):
        """Test basic SPDXInfo creation."""
        spdx_info = SPDXInfo(
            license_identifier="MIT",
            copyright_text="Copyright (c) 2023 Example Corp",
            project_attribution="Example Project",
            spdx_version="SPDX-2.2",
        )

        assert spdx_info.license_identifier == "MIT"
        assert spdx_info.copyright_text == "Copyright (c) 2023 Example Corp"
        assert spdx_info.project_attribution == "Example Project"
        assert spdx_info.spdx_version == "SPDX-2.2"
        assert spdx_info.declaration_type == SPDXDeclarationType.NONE

    def test_spdx_info_validation(self):
        """Test SPDXInfo validation methods."""
        # Valid SPDX info
        spdx_info = SPDXInfo(
            license_identifier="MIT",
            copyright_text="Copyright (c) 2023 Example Corp",
        )
        assert spdx_info.is_valid() is True
        assert spdx_info.has_minimal_info() is True

        # Invalid SPDX info (no license)
        spdx_info = SPDXInfo()
        assert spdx_info.is_valid() is False
        assert spdx_info.has_minimal_info() is False

        # SPDX info with validation errors
        spdx_info = SPDXInfo(
            license_identifier="MIT",
            validation_errors=[
                ValidationError(
                    severity=ValidationSeverity.ERROR,
                    message="Test error"
                )
            ]
        )
        assert spdx_info.is_valid() is False

    def test_spdx_info_copyright_years(self):
        """Test copyright year extraction."""
        spdx_info = SPDXInfo(
            copyright_text="Copyright (c) 2023 Example Corp"
        )
        years = spdx_info.get_copyright_years()
        assert years == [2023]

        spdx_info = SPDXInfo(
            copyright_text="Copyright (c) 2020-2023 Example Corp"
        )
        years = spdx_info.get_copyright_years()
        assert 2020 in years
        assert 2023 in years

    def test_spdx_info_serialization(self):
        """Test SPDXInfo serialization/deserialization."""
        spdx_info = SPDXInfo(
            license_identifier="MIT",
            copyright_text="Copyright (c) 2023 Example Corp",
            project_attribution="Example Project",
            spdx_version="SPDX-2.2",
            additional_tags={"homepage": "https://example.com"},
            declaration_type=SPDXDeclarationType.HEADER,
        )

        # Convert to dict
        data = spdx_info.to_dict()
        assert data["license_identifier"] == "MIT"
        assert data["copyright_text"] == "Copyright (c) 2023 Example Corp"
        assert data["declaration_type"] == "header"
        assert data["additional_tags"]["homepage"] == "https://example.com"

        # Convert back from dict
        spdx_info2 = SPDXInfo.from_dict(data)
        assert spdx_info2.license_identifier == "MIT"
        assert spdx_info2.copyright_text == "Copyright (c) 2023 Example Corp"
        assert spdx_info2.declaration_type == SPDXDeclarationType.HEADER


class TestFileInfo:
    """Test FileInfo model."""

    def test_file_info_creation(self):
        """Test basic FileInfo creation."""
        file_info = FileInfo(
            filepath=Path("test.py"),
            language="python",
            content="print('hello')",
            encoding="utf-8",
            line_endings="\n",
            has_shebang=False,
            size=14,
        )

        assert file_info.filepath == Path("test.py")
        assert file_info.language == "python"
        assert file_info.content == "print('hello')"
        assert file_info.encoding == "utf-8"
        assert file_info.line_endings == "\n"
        assert file_info.has_shebang is False
        assert file_info.size == 14

    def test_file_info_methods(self):
        """Test FileInfo utility methods."""
        file_info = FileInfo(
            filepath=Path("/home/user/project/test.py"),
            language="python",
            content="print('hello')",
        )

        assert file_info.get_file_extension() == ".py"
        assert file_info.get_relative_path(Path("/home/user")) == Path("project/test.py")

        # Test SPDX-related methods
        assert file_info.has_spdx_declaration() is False
        assert file_info.needs_spdx_correction() is True

        # Add SPDX info
        file_info.spdx_info = SPDXInfo(license_identifier="MIT")
        assert file_info.has_spdx_declaration() is True
        assert file_info.needs_spdx_correction() is False

    def test_file_info_serialization(self):
        """Test FileInfo serialization/deserialization."""
        file_info = FileInfo(
            filepath=Path("test.py"),
            language="python",
            content="print('hello')",
            encoding="utf-8",
            size=14,
        )

        # Convert to dict
        data = file_info.to_dict()
        assert data["filepath"] == "test.py"
        assert data["language"] == "python"
        assert data["encoding"] == "utf-8"
        assert data["size"] == 14

        # Convert back from dict
        file_info2 = FileInfo.from_dict(data)
        assert file_info2.filepath == Path("test.py")
        assert file_info2.language == "python"
        assert file_info2.encoding == "utf-8"
        assert file_info2.size == 14


class TestValidationResult:
    """Test ValidationResult model."""

    def test_validation_result_creation(self):
        """Test basic ValidationResult creation."""
        result = ValidationResult(is_valid=True)
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
        assert len(result.suggestions) == 0

    def test_validation_result_add_methods(self):
        """Test adding errors, warnings, and suggestions."""
        result = ValidationResult(is_valid=True)

        # Add error
        error = ValidationError(
            severity=ValidationSeverity.ERROR,
            message="Test error"
        )
        result.add_error(error)
        assert len(result.errors) == 1
        assert result.is_valid is False

        # Add warning
        warning = ValidationError(
            severity=ValidationSeverity.WARNING,
            message="Test warning"
        )
        result.add_warning(warning)
        assert len(result.warnings) == 1

        # Add suggestion
        result.add_suggestion("Test suggestion")
        assert len(result.suggestions) == 1

    def test_validation_result_summary(self):
        """Test validation result summary methods."""
        result = ValidationResult(is_valid=False)
        result.add_error(ValidationError(severity=ValidationSeverity.ERROR, message="Error 1"))
        result.add_error(ValidationError(severity=ValidationSeverity.ERROR, message="Error 2"))
        result.add_warning(ValidationError(severity=ValidationSeverity.WARNING, message="Warning 1"))
        result.add_suggestion("Suggestion 1")

        summary = result.get_summary()
        assert summary["total_errors"] == 2
        assert summary["total_warnings"] == 1
        assert summary["total_suggestions"] == 1
        assert summary["is_valid"] is False

        all_issues = result.get_all_issues()
        assert len(all_issues) == 3  # 2 errors + 1 warning


class TestValidationError:
    """Test ValidationError model."""

    def test_validation_error_creation(self):
        """Test basic ValidationError creation."""
        error = ValidationError(
            severity=ValidationSeverity.ERROR,
            message="Test error message",
            line_number=10,
            column=5,
            rule_id="test_rule",
            suggestion="Test suggestion"
        )

        assert error.severity == ValidationSeverity.ERROR
        assert error.message == "Test error message"
        assert error.line_number == 10
        assert error.column == 5
        assert error.rule_id == "test_rule"
        assert error.suggestion == "Test suggestion"

    def test_validation_error_validation(self):
        """Test ValidationError validation."""
        # Valid error
        error = ValidationError(
            severity=ValidationSeverity.ERROR,
            message="Test error"
        )
        assert error.message == "Test error"

        # Invalid error (empty message)
        with pytest.raises(ValueError, match="Validation error message cannot be empty"):
            ValidationError(
                severity=ValidationSeverity.ERROR,
                message=""
            )


class TestCorrectionResult:
    """Test CorrectionResult model."""

    def test_correction_result_creation(self):
        """Test basic CorrectionResult creation."""
        result = CorrectionResult(
            original_content="original",
            corrected_content="corrected",
            success=True,
            backup_created=True,
            backup_path=Path("backup.txt")
        )

        assert result.original_content == "original"
        assert result.corrected_content == "corrected"
        assert result.success is True
        assert result.backup_created is True
        assert result.backup_path == Path("backup.txt")
        assert len(result.changes_made) == 0

    def test_correction_result_methods(self):
        """Test CorrectionResult utility methods."""
        result = CorrectionResult(
            original_content="original",
            corrected_content="corrected",
            success=True
        )

        # Add changes
        result.add_change("Added SPDX header")
        result.add_change("Fixed copyright format")
        assert len(result.changes_made) == 2
        assert result.has_changes() is True

        # Test with no changes
        result2 = CorrectionResult(
            original_content="same",
            corrected_content="same",
            success=True
        )
        assert result2.has_changes() is False

    def test_correction_result_summary(self):
        """Test correction result summary."""
        result = CorrectionResult(
            original_content="original",
            corrected_content="corrected",
            success=True,
            backup_created=True
        )
        result.add_change("Change 1")
        result.add_change("Change 2")

        summary = result.get_summary()
        assert summary["success"] is True
        assert summary["changes_made"] == 2
        assert summary["backup_created"] is True
        assert summary["has_changes"] is True


class TestScanResult:
    """Test ScanResult model."""

    def test_scan_result_creation(self):
        """Test basic ScanResult creation."""
        file_info = FileInfo(
            filepath=Path("test.py"),
            language="python",
            content="print('hello')"
        )

        validation_result = ValidationResult(is_valid=True)

        scan_result = ScanResult(
            file_info=file_info,
            validation_result=validation_result
        )

        assert scan_result.file_info == file_info
        assert scan_result.validation_result == validation_result
        assert scan_result.correction_result is None
        assert scan_result.is_valid() is True
        assert scan_result.needs_correction() is True  # No SPDX info

    def test_scan_result_with_correction(self):
        """Test ScanResult with correction."""
        file_info = FileInfo(
            filepath=Path("test.py"),
            language="python",
            content="print('hello')"
        )
        file_info.spdx_info = SPDXInfo(license_identifier="MIT")  # Valid SPDX

        validation_result = ValidationResult(is_valid=True)

        correction_result = CorrectionResult(
            original_content="original",
            corrected_content="corrected",
            success=True
        )
        correction_result.add_change("Added SPDX header")

        scan_result = ScanResult(
            file_info=file_info,
            validation_result=validation_result,
            correction_result=correction_result
        )

        assert scan_result.is_valid() is True
        assert scan_result.needs_correction() is False  # Already valid
        assert scan_result.was_corrected() is True


class TestScanSummary:
    """Test ScanSummary model."""

    def test_scan_summary_creation(self):
        """Test basic ScanSummary creation."""
        summary = ScanSummary()
        assert summary.total_files == 0
        assert summary.valid_files == 0
        assert summary.invalid_files == 0
        assert summary.corrected_files == 0
        assert summary.failed_corrections == 0
        assert summary.skipped_files == 0

    def test_scan_summary_add_result(self):
        """Test adding results to summary."""
        summary = ScanSummary()

        # Add valid result
        file_info = FileInfo(filepath=Path("valid.py"), language="python", content="valid")
        file_info.spdx_info = SPDXInfo(license_identifier="MIT")  # Valid
        validation_result = ValidationResult(is_valid=True)
        valid_result = ScanResult(file_info=file_info, validation_result=validation_result)
        summary.add_result(valid_result)

        assert summary.total_files == 1
        assert summary.valid_files == 1
        assert summary.invalid_files == 0

        # Add invalid result
        file_info = FileInfo(filepath=Path("invalid.py"), language="python", content="invalid")
        validation_result = ValidationResult(is_valid=False)
        invalid_result = ScanResult(file_info=file_info, validation_result=validation_result)
        summary.add_result(invalid_result)

        assert summary.total_files == 2
        assert summary.valid_files == 1
        assert summary.invalid_files == 1

    def test_scan_summary_rates(self):
        """Test success and correction rates."""
        summary = ScanSummary()

        # Add some results
        for i in range(10):
            file_info = FileInfo(filepath=Path(f"file{i}.py"), language="python", content="test")
            if i < 7:  # 70% valid
                file_info.spdx_info = SPDXInfo(license_identifier="MIT")
                validation_result = ValidationResult(is_valid=True)
            else:
                validation_result = ValidationResult(is_valid=False)

            result = ScanResult(file_info=file_info, validation_result=validation_result)
            summary.add_result(result)

        assert summary.get_success_rate() == 70.0
        assert summary.get_correction_rate() == 0.0  # No corrections yet

    def test_scan_summary_serialization(self):
        """Test ScanSummary serialization."""
        summary = ScanSummary(
            total_files=10,
            valid_files=7,
            invalid_files=3,
            corrected_files=2,
            failed_corrections=1,
            skipped_files=0
        )

        data = summary.to_dict()
        assert data["total_files"] == 10
        assert data["valid_files"] == 7
        assert data["invalid_files"] == 3
        assert data["corrected_files"] == 2
        assert data["failed_corrections"] == 1
        assert data["success_rate"] == 70.0
        assert data["correction_rate"] == 66.67  # 2/3 * 100