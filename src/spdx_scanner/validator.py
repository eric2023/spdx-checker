"""
SPDX validator component for SPDX Scanner.

This module provides functionality to validate SPDX license declarations
against the SPDX specification and UnionTech requirements.
"""

import json
import re
from typing import List, Optional, Dict, Set, Any
from pathlib import Path
import logging
from datetime import datetime

from .models import SPDXInfo, ValidationResult, ValidationError, ValidationSeverity


logger = logging.getLogger(__name__)


class SPDXLicenseDatabase:
    """SPDX license database for validation."""

    # Core SPDX licenses (simplified list for validation)
    CORE_LICENSES = {
        # Popular OSI-approved licenses
        'MIT': {
            'name': 'MIT License',
            'is_osi_approved': True,
            'is_fsf_libre': True,
            'category': 'Permissive',
        },
        'Apache-2.0': {
            'name': 'Apache License 2.0',
            'is_osi_approved': True,
            'is_fsf_libre': True,
            'category': 'Permissive',
        },
        'GPL-2.0': {
            'name': 'GNU General Public License v2.0 only',
            'is_osi_approved': True,
            'is_fsf_libre': True,
            'category': 'Copyleft',
        },
        'GPL-2.0+': {
            'name': 'GNU General Public License v2.0 or later',
            'is_osi_approved': True,
            'is_fsf_libre': True,
            'category': 'Copyleft',
        },
        'GPL-3.0': {
            'name': 'GNU General Public License v3.0 only',
            'is_osi_approved': True,
            'is_fsf_libre': True,
            'category': 'Copyleft',
        },
        'GPL-3.0+': {
            'name': 'GNU General Public License v3.0 or later',
            'is_osi_approved': True,
            'is_fsf_libre': True,
            'category': 'Copyleft',
        },
        'LGPL-2.1': {
            'name': 'GNU Lesser General Public License v2.1 only',
            'is_osi_approved': True,
            'is_fsf_libre': True,
            'category': 'Weak Copyleft',
        },
        'LGPL-2.1+': {
            'name': 'GNU Lesser General Public License v2.1 or later',
            'is_osi_approved': True,
            'is_fsf_libre': True,
            'category': 'Weak Copyleft',
        },
        'LGPL-3.0': {
            'name': 'GNU Lesser General Public License v3.0 only',
            'is_osi_approved': True,
            'is_fsf_libre': True,
            'category': 'Weak Copyleft',
        },
        'LGPL-3.0+': {
            'name': 'GNU Lesser General Public License v3.0 or later',
            'is_osi_approved': True,
            'is_fsf_libre': True,
            'category': 'Weak Copyleft',
        },
        'BSD-2-Clause': {
            'name': 'BSD 2-Clause License',
            'is_osi_approved': True,
            'is_fsf_libre': True,
            'category': 'Permissive',
        },
        'BSD-3-Clause': {
            'name': 'BSD 3-Clause License',
            'is_osi_approved': True,
            'is_fsf_libre': True,
            'category': 'Permissive',
        },
        'MPL-2.0': {
            'name': 'Mozilla Public License 2.0',
            'is_osi_approved': True,
            'is_fsf_libre': True,
            'category': 'Weak Copyleft',
        },
        'EPL-2.0': {
            'name': 'Eclipse Public License 2.0',
            'is_osi_approved': True,
            'is_fsf_libre': True,
            'category': 'Weak Copyleft',
        },
        'CC0-1.0': {
            'name': 'Creative Commons Zero v1.0 Universal',
            'is_osi_approved': False,
            'is_fsf_libre': True,
            'category': 'Public Domain',
        },
        'Unlicense': {
            'name': 'The Unlicense',
            'is_osi_approved': True,
            'is_fsf_libre': True,
            'category': 'Public Domain',
        },
    }

    # License exceptions (for "WITH" expressions)
    LICENSE_EXCEPTIONS = {
        'Classpath-exception-2.0',
        'GPL-CC-1.0',
        'LLVM-exception',
        'Autoconf-exception-3.0',
        'Font-exception-2.0',
        'OCaml-LGPL-linking-exception',
        'Qt-GPL-exception-1.0',
        'Universal-FOSS-exception-1.0',
    }

    @classmethod
    def is_valid_license_id(cls, license_id: str) -> bool:
        """Check if license ID is valid."""
        # Handle simple license IDs
        if license_id in cls.CORE_LICENSES:
            return True

        # Handle "WITH" expressions (license WITH exception)
        if ' WITH ' in license_id:
            parts = license_id.split(' WITH ')
            if len(parts) == 2:
                base_license = parts[0].strip()
                exception = parts[1].strip()
                return (
                    base_license in cls.CORE_LICENSES and
                    exception in cls.LICENSE_EXCEPTIONS
                )

        # Handle "OR" expressions (license disjunction)
        if ' OR ' in license_id:
            licenses = [part.strip() for part in license_id.split(' OR ')]
            return all(lic in cls.CORE_LICENSES for lic in licenses)

        # Handle "AND" expressions (license conjunction)
        if ' AND ' in license_id:
            licenses = [part.strip() for part in license_id.split(' AND ')]
            return all(lic in cls.CORE_LICENSES for lic in licenses)

        # Handle parentheses for grouping
        license_id = license_id.strip()
        if license_id.startswith('(') and license_id.endswith(')'):
            return cls.is_valid_license_id(license_id[1:-1])

        return False

    @classmethod
    def get_license_info(cls, license_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a license."""
        # Handle simple license IDs
        if license_id in cls.CORE_LICENSES:
            return cls.CORE_LICENSES[license_id]

        # For complex expressions, return basic info
        if any(op in license_id for op in [' OR ', ' AND ', ' WITH ']):
            return {
                'name': f'Complex License Expression: {license_id}',
                'is_osi_approved': False,  # Complex expressions need individual evaluation
                'is_fsf_libre': False,
                'category': 'Complex',
            }

        return None


class SPDXValidator:
    """SPDX license declaration validator."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize validator with configuration."""
        self.config = config or {}
        self.license_db = SPDXLicenseDatabase()
        self.validation_rules = self._load_validation_rules()

    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load validation rules from configuration."""
        default_rules = {
            'require_license_identifier': True,
            'require_copyright': True,
            'require_project_attribution': False,
            'allow_unknown_licenses': False,
            'require_osi_approved': False,
            'require_spdx_version': False,
            'min_copyright_year': 1970,
            'max_copyright_year': datetime.now().year + 1,
            'copyright_format': 'standard',  # 'standard', 'flexible', 'any'
            'license_format': 'strict',  # 'strict', 'flexible'
        }

        # Override with config
        default_rules.update(self.config.get('validation_rules', {}))
        return default_rules

    def validate(self, spdx_info: SPDXInfo) -> ValidationResult:
        """Validate SPDX information."""
        result = ValidationResult(is_valid=True)
        start_time = datetime.now()

        try:
            # Validate license identifier
            self._validate_license_identifier(spdx_info, result)

            # Validate copyright
            self._validate_copyright(spdx_info, result)

            # Validate project attribution
            self._validate_project_attribution(spdx_info, result)

            # Validate SPDX version
            self._validate_spdx_version(spdx_info, result)

            # Validate additional tags
            self._validate_additional_tags(spdx_info, result)

            # Check for recommended practices
            self._validate_best_practices(spdx_info, result)

        except Exception as e:
            logger.error(f"Validation error: {e}")
            result.add_error(ValidationError(
                severity=ValidationSeverity.ERROR,
                message=f"Validation failed: {str(e)}",
                rule_id="validation_error"
            ))

        # Calculate validation time
        end_time = datetime.now()
        result.validation_time = (end_time - start_time).total_seconds()

        return result

    def _validate_license_identifier(self, spdx_info: SPDXInfo, result: ValidationResult) -> None:
        """Validate license identifier."""
        if self.validation_rules['require_license_identifier']:
            if not spdx_info.license_identifier:
                result.add_error(ValidationError(
                    severity=ValidationSeverity.ERROR,
                    message="Missing required SPDX license identifier",
                    rule_id="missing_license_identifier",
                    suggestion="Add 'SPDX-License-Identifier: [LICENSE-ID]' to your file header"
                ))
                return

        if spdx_info.license_identifier:
            license_id = spdx_info.license_identifier.strip()

            # Basic format validation
            if not self._is_valid_license_format(license_id):
                result.add_error(ValidationError(
                    severity=ValidationSeverity.ERROR,
                    message=f"Invalid SPDX license identifier format: {license_id}",
                    rule_id="invalid_license_format",
                    suggestion="Use a valid SPDX license identifier format"
                ))

            # Check against license database
            if not self.license_db.is_valid_license_id(license_id):
                if self.validation_rules['allow_unknown_licenses']:
                    result.add_warning(ValidationError(
                        severity=ValidationSeverity.WARNING,
                        message=f"Unknown or unregistered SPDX license identifier: {license_id}",
                        rule_id="unknown_license_identifier",
                        suggestion="Consider using a license from the SPDX license list"
                    ))
                else:
                    result.add_error(ValidationError(
                        severity=ValidationSeverity.ERROR,
                        message=f"Invalid SPDX license identifier: {license_id}",
                        rule_id="invalid_license_identifier",
                        suggestion="Use a valid SPDX license identifier from https://spdx.org/licenses/"
                    ))

            # Check OSI approval if required
            if self.validation_rules['require_osi_approved']:
                license_info = self.license_db.get_license_info(license_id)
                if license_info and not license_info.get('is_osi_approved', False):
                    result.add_warning(ValidationError(
                        severity=ValidationSeverity.WARNING,
                        message=f"License is not OSI approved: {license_id}",
                        rule_id="non_osi_license",
                        suggestion="Consider using an OSI approved license"
                    ))

    def _validate_copyright(self, spdx_info: SPDXInfo, result: ValidationResult) -> None:
        """Validate copyright information."""
        if self.validation_rules['require_copyright']:
            if not spdx_info.copyright_text:
                result.add_error(ValidationError(
                    severity=ValidationSeverity.ERROR,
                    message="Missing required copyright information",
                    rule_id="missing_copyright",
                    suggestion="Add copyright information in format: 'Copyright (c) [year] [holder]'"
                ))
                return

        if spdx_info.copyright_text:
            copyright_text = spdx_info.copyright_text.strip()

            # Validate copyright format
            if not self._is_valid_copyright_format(copyright_text):
                severity = ValidationSeverity.WARNING
                if self.validation_rules['copyright_format'] == 'standard':
                    severity = ValidationSeverity.ERROR

                result.add_error(ValidationError(
                    severity=severity,
                    message=f"Copyright format may be invalid: {copyright_text}",
                    rule_id="invalid_copyright_format",
                    suggestion="Use format: 'Copyright (c) [year] [holder]'"
                ))

            # Validate copyright years
            years = self._extract_copyright_years(copyright_text)
            if years:
                min_year = self.validation_rules['min_copyright_year']
                max_year = self.validation_rules['max_copyright_year']
                current_year = datetime.now().year

                for year in years:
                    if year < min_year or year > max_year:
                        result.add_warning(ValidationError(
                            severity=ValidationSeverity.WARNING,
                            message=f"Copyright year {year} seems unusual",
                            rule_id="unusual_copyright_year",
                            suggestion=f"Copyright year should be between {min_year} and {max_year}"
                        ))
                    elif year > current_year:
                        result.add_warning(ValidationError(
                            severity=ValidationSeverity.WARNING,
                            message=f"Copyright year {year} is in the future",
                            rule_id="future_copyright_year",
                            suggestion="Copyright year should not be in the future"
                        ))

    def _validate_project_attribution(self, spdx_info: SPDXInfo, result: ValidationResult) -> None:
        """Validate project attribution."""
        if self.validation_rules['require_project_attribution']:
            if not spdx_info.project_attribution:
                result.add_error(ValidationError(
                    severity=ValidationSeverity.ERROR,
                    message="Missing required project attribution",
                    rule_id="missing_project_attribution",
                    suggestion="Add project name or attribution information"
                ))

        if spdx_info.project_attribution:
            attribution = spdx_info.project_attribution.strip()
            if len(attribution) < 2:
                result.add_warning(ValidationError(
                    severity=ValidationSeverity.WARNING,
                    message="Project attribution seems too short",
                    rule_id="short_project_attribution",
                    suggestion="Provide more descriptive project attribution"
                ))

    def _validate_spdx_version(self, spdx_info: SPDXInfo, result: ValidationResult) -> None:
        """Validate SPDX version."""
        if self.validation_rules['require_spdx_version']:
            if not spdx_info.spdx_version:
                result.add_error(ValidationError(
                    severity=ValidationSeverity.ERROR,
                    message="Missing required SPDX version",
                    rule_id="missing_spdx_version",
                    suggestion="Add 'SPDX-Version: [version]' to your file header"
                ))

        if spdx_info.spdx_version:
            version = spdx_info.spdx_version.strip()
            if not self._is_valid_spdx_version(version):
                result.add_warning(ValidationError(
                    severity=ValidationSeverity.WARNING,
                    message=f"Unusual SPDX version format: {version}",
                    rule_id="unusual_spdx_version",
                    suggestion="Use format: 'SPDX-2.2' or similar"
                ))

    def _validate_additional_tags(self, spdx_info: SPDXInfo, result: ValidationResult) -> None:
        """Validate additional SPDX tags."""
        # Validate contributor information if present
        if 'contributors' in spdx_info.additional_tags:
            contributors = spdx_info.additional_tags['contributors']
            if not contributors.strip():
                result.add_warning(ValidationError(
                    severity=ValidationSeverity.WARNING,
                    message="Empty contributor information",
                    rule_id="empty_contributors",
                    suggestion="Remove empty contributor tag or add contributor names"
                ))

        # Validate download location if present
        if 'download_location' in spdx_info.additional_tags:
            download_location = spdx_info.additional_tags['download_location']
            if not self._is_valid_url(download_location):
                result.add_warning(ValidationError(
                    severity=ValidationSeverity.WARNING,
                    message=f"Invalid download location URL: {download_location}",
                    rule_id="invalid_download_location",
                    suggestion="Use a valid URL for download location"
                ))

        # Validate homepage if present
        if 'homepage' in spdx_info.additional_tags:
            homepage = spdx_info.additional_tags['homepage']
            if not self._is_valid_url(homepage):
                result.add_warning(ValidationError(
                    severity=ValidationSeverity.WARNING,
                    message=f"Invalid homepage URL: {homepage}",
                    rule_id="invalid_homepage",
                    suggestion="Use a valid URL for homepage"
                ))

    def _validate_best_practices(self, spdx_info: SPDXInfo, result: ValidationResult) -> None:
        """Validate SPDX best practices."""
        # Check for complete license information
        if spdx_info.license_identifier and not spdx_info.copyright_text:
            result.add_suggestion("Consider adding copyright information along with license identifier")

        if spdx_info.copyright_text and not spdx_info.license_identifier:
            result.add_suggestion("Consider adding license identifier along with copyright information")

        # Check for SPDX version (recommended)
        if not spdx_info.spdx_version:
            result.add_suggestion("Consider adding SPDX version for clarity")

        # Check license identifier format
        if spdx_info.license_identifier:
            if spdx_info.license_identifier != spdx_info.license_identifier.strip():
                result.add_warning(ValidationError(
                    severity=ValidationSeverity.WARNING,
                    message="License identifier contains leading/trailing whitespace",
                    rule_id="license_whitespace",
                    suggestion="Remove leading/trailing whitespace from license identifier"
                ))

    def _is_valid_license_format(self, license_id: str) -> bool:
        """Check if license identifier has valid format."""
        # Basic SPDX license identifier format validation
        # Should contain only alphanumeric characters, hyphens, dots, plus signs, and parentheses
        valid_chars = re.match(r'^[A-Za-z0-9\-\+\.\(\)\s]+$', license_id)
        if not valid_chars:
            return False

        # Should not be empty or just whitespace
        if not license_id.strip():
            return False

        # Should not contain consecutive operators without proper grouping
        if re.search(r'(OR\s+OR|AND\s+AND|WITH\s+WITH)', license_id):
            return False

        return True

    def _is_valid_copyright_format(self, copyright_text: str) -> bool:
        """Check if copyright text has valid format."""
        # Standard copyright format: "Copyright (c) [year(s)] [holder]"
        standard_pattern = r'^Copyright\s*\(c\)\s*[0-9\-\,\s]+\s+.+$'
        if re.match(standard_pattern, copyright_text, re.IGNORECASE):
            return True

        # Alternative formats (more flexible)
        alternative_patterns = [
            r'^©\s*[0-9\-\,\s]+\s+.+$',  # "© [year(s)] [holder]"
            r'^Copyright\s+[0-9\-\,\s]+\s+.+$',  # "Copyright [year(s)] [holder]"
            r'^©\s+[0-9\-\,\s]+\s+.+$',  # "© [year(s)] [holder]"
        ]

        for pattern in alternative_patterns:
            if re.match(pattern, copyright_text, re.IGNORECASE):
                return True

        return False

    def _is_valid_spdx_version(self, version: str) -> bool:
        """Check if SPDX version has valid format."""
        version_pattern = r'^SPDX-[0-9]+\.[0-9]+$'
        return bool(re.match(version_pattern, version, re.IGNORECASE))

    def _is_valid_url(self, url: str) -> bool:
        """Check if string is a valid URL."""
        url_pattern = r'^https?://[A-Za-z0-9\-\._~:/?#\[\]@!$&\'()*+,;=]+$'
        return bool(re.match(url_pattern, url))

    def _extract_copyright_years(self, copyright_text: str) -> List[int]:
        """Extract copyright years from copyright text."""
        year_pattern = r'\b(19|20)\d{2}\b'
        years = re.findall(year_pattern, copyright_text)
        return [int(year) for year in years]

    def get_validation_rules(self) -> Dict[str, Any]:
        """Get current validation rules."""
        return self.validation_rules.copy()

    def update_validation_rule(self, rule: str, value: Any) -> None:
        """Update a validation rule."""
        if rule in self.validation_rules:
            self.validation_rules[rule] = value
        else:
            logger.warning(f"Unknown validation rule: {rule}")


def create_default_validator(config: Optional[Dict[str, Any]] = None) -> SPDXValidator:
    """Create a default SPDX validator instance."""
    return SPDXValidator(config)