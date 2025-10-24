"""
Tests for SPDX Scanner validator component.
"""

import pytest
from datetime import datetime
from spdx_scanner.validator import SPDXLicenseDatabase, SPDXValidator, create_default_validator
from spdx_scanner.models import SPDXInfo, ValidationResult, ValidationError, ValidationSeverity


class TestSPDXLicenseDatabase:
    """Test SPDX license database."""

    def test_is_valid_license_id_simple(self):
        """Test validation of simple license IDs."""
        db = SPDXLicenseDatabase()

        # Valid licenses
        assert db.is_valid_license_id("MIT") is True
        assert db.is_valid_license_id("Apache-2.0") is True
        assert db.is_valid_license_id("GPL-3.0") is True
        assert db.is_valid_license_id("BSD-3-Clause") is True

        # Invalid licenses
        assert db.is_valid_license_id("INVALID-LICENSE") is False
        assert db.is_valid_license_id("") is False
        assert db.is_valid_license_id("Made-Up-License") is False

    def test_is_valid_license_id_with_exception(self):
        """Test validation of licenses with exceptions."""
        db = SPDXLicenseDatabase()

        # Valid license with exception
        assert db.is_valid_license_id("GPL-3.0 WITH Classpath-exception-2.0") is True
        assert db.is_valid_license_id("GPL-2.0 WITH GPL-CC-1.0") is True

        # Invalid exception
        assert db.is_valid_license_id("MIT WITH Invalid-exception") is False

    def test_is_valid_license_id_with_or(self):
        """Test validation of licenses with OR expressions."""
        db = SPDXLicenseDatabase()

        # Valid OR expressions
        assert db.is_valid_license_id("MIT OR Apache-2.0") is True
        assert db.is_valid_license_id("GPL-3.0 OR BSD-3-Clause") is True
        assert db.is_valid_license_id("MIT OR Apache-2.0 OR BSD-3-Clause") is True

        # Invalid OR expressions
        assert db.is_valid_license_id("MIT OR Invalid-License") is False
        assert db.is_valid_license_id("Invalid-License OR Apache-2.0") is False

    def test_is_valid_license_id_with_and(self):
        """Test validation of licenses with AND expressions."""
        db = SPDXLicenseDatabase()

        # Valid AND expressions
        assert db.is_valid_license_id("MIT AND Apache-2.0") is True
        assert db.is_valid_license_id("GPL-3.0 AND BSD-3-Clause") is True

        # Invalid AND expressions
        assert db.is_valid_license_id("MIT AND Invalid-License") is False
        assert db.is_valid_license_id("Invalid-License AND Apache-2.0") is False

    def test_is_valid_license_id_with_parentheses(self):
        """Test validation of licenses with parentheses."""
        db = SPDXLicenseDatabase()

        # Valid with parentheses
        assert db.is_valid_license_id("(MIT OR Apache-2.0)") is True
        assert db.is_valid_license_id("(MIT AND Apache-2.0) OR BSD-3-Clause") is True

        # Invalid with parentheses
        assert db.is_valid_license_id("(Invalid-License)") is False

    def test_is_valid_license_id_complex_expressions(self):
        """Test validation of complex license expressions."""
        db = SPDXLicenseDatabase()

        # Complex but valid expressions
        assert db.is_valid_license_id("MIT OR (Apache-2.0 AND BSD-3-Clause)") is True
        assert db.is_valid_license_id("GPL-3.0 WITH Classpath-exception-2.0 OR MIT") is True

    def test_get_license_info(self):
        """Test getting license information."""
        db = SPDXLicenseDatabase()

        # Get info for known license
        info = db.get_license_info("MIT")
        assert info is not None
        assert info['name'] == "MIT License"
        assert info['is_osi_approved'] is True
        assert info['is_fsf_libre'] is True
        assert info['category'] == "Permissive"

        # Get info for unknown license
        info = db.get_license_info("UNKNOWN-LICENSE")
        assert info is None

        # Get info for complex expression
        info = db.get_license_info("MIT OR Apache-2.0")
        assert info is not None
        assert "Complex License Expression" in info['name']


class TestSPDXValidator:
    """Test SPDX validator."""

    def test_validator_initialization(self):
        """Test validator initialization."""
        validator = SPDXValidator()
        assert validator.config == {}
        assert validator.license_db is not None
        assert validator.validation_rules is not None

    def test_validator_with_config(self):
        """Test validator initialization with configuration."""
        config = {
            'validation_rules': {
                'require_license_identifier': False,
                'require_copyright': False,
                'allow_unknown_licenses': True,
            }
        }
        validator = SPDXValidator(config)
        assert validator.validation_rules['require_license_identifier'] is False
        assert validator.validation_rules['require_copyright'] is False
        assert validator.validation_rules['allow_unknown_licenses'] is True

    def test_validate_valid_spdx_info(self):
        """Test validation of valid SPDX information."""
        validator = SPDXValidator()

        spdx_info = SPDXInfo(
            license_identifier="MIT",
            copyright_text="Copyright (c) 2023 Example Corp",
            project_attribution="Example Project",
            spdx_version="SPDX-2.2"
        )

        result = validator.validate(spdx_info)

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_validate_missing_license_identifier(self):
        """Test validation with missing license identifier."""
        validator = SPDXValidator()

        spdx_info = SPDXInfo(
            copyright_text="Copyright (c) 2023 Example Corp",
            project_attribution="Example Project",
        )

        result = validator.validate(spdx_info)

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert any("Missing required SPDX license identifier" in error.message for error in result.errors)

    def test_validate_invalid_license_identifier(self):
        """Test validation with invalid license identifier."""
        validator = SPDXValidator()

        spdx_info = SPDXInfo(
            license_identifier="INVALID-LICENSE",
            copyright_text="Copyright (c) 2023 Example Corp",
        )

        result = validator.validate(spdx_info)

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert any("Invalid SPDX license identifier" in error.message for error in result.errors)

    def test_validate_unknown_license_with_allow_unknown(self):
        """Test validation with unknown license when allowed."""
        config = {
            'validation_rules': {
                'allow_unknown_licenses': True,
            }
        }
        validator = SPDXValidator(config)

        spdx_info = SPDXInfo(
            license_identifier="CUSTOM-LICENSE",
            copyright_text="Copyright (c) 2023 Example Corp",
        )

        result = validator.validate(spdx_info)

        assert result.is_valid is True  # Should be valid when unknown licenses are allowed
        assert len(result.warnings) == 1
        assert any("Unknown or unregistered SPDX license identifier" in warning.message for warning in result.warnings)

    def test_validate_missing_copyright(self):
        """Test validation with missing copyright."""
        validator = SPDXValidator()

        spdx_info = SPDXInfo(
            license_identifier="MIT",
            project_attribution="Example Project",
        )

        result = validator.validate(spdx_info)

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert any("Missing required copyright information" in error.message for error in result.errors)

    def test_validate_invalid_copyright_format(self):
        """Test validation with invalid copyright format."""
        validator = SPDXValidator()

        spdx_info = SPDXInfo(
            license_identifier="MIT",
            copyright_text="Invalid copyright format",
        )

        result = validator.validate(spdx_info)

        # Should have a warning about copyright format
        assert len(result.warnings) >= 1
        assert any("Copyright format may be invalid" in warning.message for warning in result.warnings)

    def test_validate_copyright_year_validation(self):
        """Test validation of copyright years."""
        validator = SPDXValidator()

        # Future year
        future_year = datetime.now().year + 5
        spdx_info = SPDXInfo(
            license_identifier="MIT",
            copyright_text=f"Copyright (c) {future_year} Example Corp",
        )

        result = validator.validate(spdx_info)

        assert len(result.warnings) >= 1
        assert any("Copyright year" in warning.message for warning in result.warnings)

        # Very old year
        spdx_info = SPDXInfo(
            license_identifier="MIT",
            copyright_text="Copyright (c) 1800 Example Corp",
        )

        result = validator.validate(spdx_info)

        assert len(result.warnings) >= 1
        assert any("Copyright year" in warning.message and "unusual" in warning.message for warning in result.warnings)

    def test_validate_project_attribution(self):
        """Test validation of project attribution."""
        config = {
            'validation_rules': {
                'require_project_attribution': True,
            }
        }
        validator = SPDXValidator(config)

        spdx_info = SPDXInfo(
            license_identifier="MIT",
            copyright_text="Copyright (c) 2023 Example Corp",
            # Missing project attribution
        )

        result = validator.validate(spdx_info)

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert any("Missing required project attribution" in error.message for error in result.errors)

    def test_validate_spdx_version(self):
        """Test validation of SPDX version."""
        config = {
            'validation_rules': {
                'require_spdx_version': True,
            }
        }
        validator = SPDXValidator(config)

        spdx_info = SPDXInfo(
            license_identifier="MIT",
            copyright_text="Copyright (c) 2023 Example Corp",
            # Missing SPDX version
        )

        result = validator.validate(spdx_info)

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert any("Missing required SPDX version" in error.message for error in result.errors)

    def test_validate_additional_tags(self):
        """Test validation of additional tags."""
        validator = SPDXValidator()

        spdx_info = SPDXInfo(
            license_identifier="MIT",
            copyright_text="Copyright (c) 2023 Example Corp",
            additional_tags={
                "homepage": "not-a-valid-url",
                "download_location": "also-invalid",
                "contributors": "",  # Empty contributors
            }
        )

        result = validator.validate(spdx_info)

        # Should have warnings about invalid URLs and empty contributors
        assert len(result.warnings) >= 2
        assert any("Invalid homepage URL" in warning.message for warning in result.warnings)
        assert any("Invalid download location URL" in warning.message for warning in result.warnings)
        assert any("Empty contributor information" in warning.message for warning in result.warnings)

    def test_validate_best_practices(self):
        """Test validation of best practices."""
        validator = SPDXValidator()

        # License without copyright
        spdx_info = SPDXInfo(
            license_identifier="MIT",
            # Missing copyright
        )

        result = validator.validate(spdx_info)

        assert len(result.suggestions) >= 1
        assert any("Consider adding copyright information" in suggestion for suggestion in result.suggestions)

        # Copyright without license
        spdx_info = SPDXInfo(
            copyright_text="Copyright (c) 2023 Example Corp",
            # Missing license
        )

        result = validator.validate(spdx_info)

        assert len(result.suggestions) >= 1
        assert any("Consider adding license identifier" in suggestion for suggestion in result.suggestions)

    def test_validate_license_whitespace(self):
        """Test validation of license identifier whitespace."""
        validator = SPDXValidator()

        spdx_info = SPDXInfo(
            license_identifier="  MIT  ",  # With whitespace
            copyright_text="Copyright (c) 2023 Example Corp",
        )

        result = validator.validate(spdx_info)

        assert len(result.warnings) >= 1
        assert any("License identifier contains leading/trailing whitespace" in warning.message for warning in result.warnings)

    def test_validation_result_summary(self):
        """Test validation result summary."""
        validator = SPDXValidator()

        spdx_info = SPDXInfo(
            license_identifier="MIT",
            copyright_text="Copyright (c) 2023 Example Corp",
        )

        result = validator.validate(spdx_info)

        summary = result.get_summary()
        assert summary["is_valid"] is True
        assert summary["total_errors"] == 0
        assert summary["total_warnings"] == 0
        assert summary["total_suggestions"] == 0

    def test_validation_result_all_issues(self):
        """Test getting all validation issues."""
        validator = SPDXValidator()

        spdx_info = SPDXInfo(
            license_identifier="INVALID-LICENSE",
            # Missing copyright
        )

        result = validator.validate(spdx_info)

        all_issues = result.get_all_issues()
        assert len(all_issues) >= 2  # At least one error for invalid license and one for missing copyright
        assert all(isinstance(issue, ValidationError) for issue in all_issues)

    def test_update_validation_rule(self):
        """Test updating validation rules."""
        validator = SPDXValidator()

        # Update existing rule
        validator.update_validation_rule('require_license_identifier', False)
        assert validator.validation_rules['require_license_identifier'] is False

        # Try to update non-existent rule
        validator.update_validation_rule('non_existent_rule', True)
        # Should not crash, but should log a warning

    def test_get_validation_rules(self):
        """Test getting validation rules."""
        validator = SPDXValidator()

        rules = validator.get_validation_rules()
        assert isinstance(rules, dict)
        assert 'require_license_identifier' in rules
        assert 'require_copyright' in rules
        assert 'allow_unknown_licenses' in rules


class TestCreateDefaultValidator:
    """Test default validator creation."""

    def test_create_default_validator(self):
        """Test creating default validator."""
        validator = create_default_validator()
        assert isinstance(validator, SPDXValidator)
        assert validator.config == {}

    def test_create_default_validator_with_config(self):
        """Test creating default validator with configuration."""
        config = {
            'validation_rules': {
                'require_license_identifier': False,
            }
        }
        validator = create_default_validator(config)
        assert isinstance(validator, SPDXValidator)
        assert validator.validation_rules['require_license_identifier'] is False