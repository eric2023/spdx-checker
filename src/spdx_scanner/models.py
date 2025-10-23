"""
Data models for SPDX Scanner.

This module defines the core data structures used throughout the application
for representing SPDX license information, file metadata, validation results,
and correction results.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any, Union


class SPDXDeclarationType(Enum):
    """Types of SPDX license declarations."""
    HEADER = "header"
    INLINE = "inline"
    SEPARATE = "separate"
    NONE = "none"


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationError:
    """Represents a validation error or warning."""
    severity: ValidationSeverity
    message: str
    line_number: Optional[int] = None
    column: Optional[int] = None
    rule_id: Optional[str] = None
    suggestion: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate the error data."""
        if not self.message:
            raise ValueError("Validation error message cannot be empty")


@dataclass
class SPDXInfo:
    """Represents SPDX license information extracted from a file."""
    license_identifier: Optional[str] = None
    copyright_text: Optional[str] = None
    project_attribution: Optional[str] = None
    spdx_version: Optional[str] = None
    additional_tags: Dict[str, str] = field(default_factory=dict)
    declaration_type: SPDXDeclarationType = SPDXDeclarationType.NONE
    validation_errors: List[ValidationError] = field(default_factory=list)
    raw_declaration: Optional[str] = None
    line_range: Optional[tuple[int, int]] = None

    def is_valid(self) -> bool:
        """Check if the SPDX information is valid."""
        return (
            self.license_identifier is not None
            and len(self.validation_errors) == 0
            and not any(error.severity == ValidationSeverity.ERROR for error in self.validation_errors)
        )

    def has_minimal_info(self) -> bool:
        """Check if minimal SPDX information is present."""
        return self.license_identifier is not None

    def get_copyright_years(self) -> List[int]:
        """Extract copyright years from copyright text."""
        if not self.copyright_text:
            return []

        import re
        year_pattern = r'\b(19|20)\d{2}\b'
        years = re.findall(year_pattern, self.copyright_text)
        return [int(year) for year in years]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "license_identifier": self.license_identifier,
            "copyright_text": self.copyright_text,
            "project_attribution": self.project_attribution,
            "spdx_version": self.spdx_version,
            "additional_tags": self.additional_tags,
            "declaration_type": self.declaration_type.value,
            "validation_errors": [
                {
                    "severity": error.severity.value,
                    "message": error.message,
                    "line_number": error.line_number,
                    "column": error.column,
                    "rule_id": error.rule_id,
                    "suggestion": error.suggestion,
                }
                for error in self.validation_errors
            ],
            "raw_declaration": self.raw_declaration,
            "line_range": self.line_range,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SPDXInfo":
        """Create SPDXInfo from dictionary."""
        validation_errors = []
        for error_data in data.get("validation_errors", []):
            error = ValidationError(
                severity=ValidationSeverity(error_data["severity"]),
                message=error_data["message"],
                line_number=error_data.get("line_number"),
                column=error_data.get("column"),
                rule_id=error_data.get("rule_id"),
                suggestion=error_data.get("suggestion"),
            )
            validation_errors.append(error)

        return cls(
            license_identifier=data.get("license_identifier"),
            copyright_text=data.get("copyright_text"),
            project_attribution=data.get("project_attribution"),
            spdx_version=data.get("spdx_version"),
            additional_tags=data.get("additional_tags", {}),
            declaration_type=SPDXDeclarationType(data.get("declaration_type", "none")),
            validation_errors=validation_errors,
            raw_declaration=data.get("raw_declaration"),
            line_range=tuple(data["line_range"]) if data.get("line_range") else None,
        )


@dataclass
class FileInfo:
    """Represents information about a source code file."""
    filepath: Path
    language: str
    content: str
    encoding: str = "utf-8"
    line_endings: str = "\n"
    has_shebang: bool = False
    spdx_info: Optional[SPDXInfo] = None
    size: int = 0
    last_modified: Optional[datetime] = None
    is_binary: bool = False
    is_empty: bool = False

    def __post_init__(self) -> None:
        """Validate and compute additional file information."""
        if not self.filepath:
            raise ValueError("Filepath cannot be empty")

        if self.size == 0 and self.content:
            self.size = len(self.content.encode(self.encoding))

        if self.last_modified is None:
            try:
                stat = self.filepath.stat()
                self.last_modified = datetime.fromtimestamp(stat.st_mtime)
            except (OSError, FileNotFoundError):
                self.last_modified = datetime.now()

    def get_file_extension(self) -> str:
        """Get the file extension."""
        return self.filepath.suffix.lower()

    def get_relative_path(self, base_path: Path) -> Path:
        """Get path relative to base path."""
        try:
            return self.filepath.relative_to(base_path)
        except ValueError:
            return self.filepath

    def has_spdx_declaration(self) -> bool:
        """Check if file has SPDX license declaration."""
        return self.spdx_info is not None and self.spdx_info.has_minimal_info()

    def needs_spdx_correction(self) -> bool:
        """Check if file needs SPDX correction."""
        if not self.has_spdx_declaration():
            return True
        return self.spdx_info is not None and not self.spdx_info.is_valid()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "filepath": str(self.filepath),
            "language": self.language,
            "encoding": self.encoding,
            "line_endings": self.line_endings,
            "has_shebang": self.has_shebang,
            "spdx_info": self.spdx_info.to_dict() if self.spdx_info else None,
            "size": self.size,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
            "is_binary": self.is_binary,
            "is_empty": self.is_empty,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileInfo":
        """Create FileInfo from dictionary."""
        spdx_info = None
        if data.get("spdx_info"):
            spdx_info = SPDXInfo.from_dict(data["spdx_info"])

        last_modified = None
        if data.get("last_modified"):
            last_modified = datetime.fromisoformat(data["last_modified"])

        return cls(
            filepath=Path(data["filepath"]),
            language=data["language"],
            content=data.get("content", ""),
            encoding=data.get("encoding", "utf-8"),
            line_endings=data.get("line_endings", "\n"),
            has_shebang=data.get("has_shebang", False),
            spdx_info=spdx_info,
            size=data.get("size", 0),
            last_modified=last_modified,
            is_binary=data.get("is_binary", False),
            is_empty=data.get("is_empty", False),
        )


@dataclass
class ValidationResult:
    """Represents the result of SPDX validation."""
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    validation_time: Optional[float] = None

    def add_error(self, error: ValidationError) -> None:
        """Add a validation error."""
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: ValidationError) -> None:
        """Add a validation warning."""
        self.warnings.append(warning)

    def add_suggestion(self, suggestion: str) -> None:
        """Add a suggestion for improvement."""
        self.suggestions.append(suggestion)

    def get_all_issues(self) -> List[ValidationError]:
        """Get all validation issues (errors and warnings)."""
        return self.errors + self.warnings

    def get_summary(self) -> Dict[str, int]:
        """Get a summary of validation results."""
        return {
            "total_errors": len(self.errors),
            "total_warnings": len(self.warnings),
            "total_suggestions": len(self.suggestions),
            "is_valid": self.is_valid,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "is_valid": self.is_valid,
            "errors": [error.__dict__ for error in self.errors],
            "warnings": [warning.__dict__ for warning in self.warnings],
            "suggestions": self.suggestions,
            "validation_time": self.validation_time,
        }


@dataclass
class CorrectionResult:
    """Represents the result of SPDX correction."""
    original_content: str
    corrected_content: str
    changes_made: List[str] = field(default_factory=list)
    backup_created: bool = False
    backup_path: Optional[Path] = None
    success: bool = False
    error_message: Optional[str] = None
    correction_time: Optional[float] = None

    def add_change(self, change_description: str) -> None:
        """Add a description of a change made."""
        self.changes_made.append(change_description)

    def has_changes(self) -> bool:
        """Check if any changes were made."""
        return len(self.changes_made) > 0 or self.original_content != self.corrected_content

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the correction."""
        return {
            "success": self.success,
            "changes_made": len(self.changes_made),
            "backup_created": self.backup_created,
            "has_changes": self.has_changes(),
            "error_message": self.error_message,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "original_content": self.original_content,
            "corrected_content": self.corrected_content,
            "changes_made": self.changes_made,
            "backup_created": self.backup_created,
            "backup_path": str(self.backup_path) if self.backup_path else None,
            "success": self.success,
            "error_message": self.error_message,
            "correction_time": self.correction_time,
        }


@dataclass
class ScanResult:
    """Represents the result of scanning a file or directory."""
    file_info: FileInfo
    validation_result: ValidationResult
    correction_result: Optional[CorrectionResult] = None
    scan_time: Optional[float] = None

    def is_valid(self) -> bool:
        """Check if the file has valid SPDX information."""
        return self.validation_result.is_valid

    def needs_correction(self) -> bool:
        """Check if the file needs SPDX correction."""
        return self.file_info.needs_spdx_correction()

    def was_corrected(self) -> bool:
        """Check if the file was successfully corrected."""
        return (
            self.correction_result is not None
            and self.correction_result.success
            and self.correction_result.has_changes()
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "file_info": self.file_info.to_dict(),
            "validation_result": self.validation_result.to_dict(),
            "correction_result": self.correction_result.to_dict() if self.correction_result else None,
            "scan_time": self.scan_time,
        }


@dataclass
class ScanSummary:
    """Summary of scanning results for multiple files."""
    total_files: int = 0
    valid_files: int = 0
    invalid_files: int = 0
    corrected_files: int = 0
    failed_corrections: int = 0
    skipped_files: int = 0
    scan_duration: Optional[float] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    def add_result(self, result: ScanResult) -> None:
        """Add a scan result to the summary."""
        self.total_files += 1

        if result.is_valid():
            self.valid_files += 1
        else:
            self.invalid_files += 1

        if result.was_corrected():
            self.corrected_files += 1
        elif result.correction_result and not result.correction_result.success:
            self.failed_corrections += 1

    def get_success_rate(self) -> float:
        """Get the percentage of valid files."""
        if self.total_files == 0:
            return 0.0
        return (self.valid_files / self.total_files) * 100

    def get_correction_rate(self) -> float:
        """Get the percentage of successfully corrected files."""
        if self.invalid_files == 0:
            return 0.0
        return (self.corrected_files / self.invalid_files) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "total_files": self.total_files,
            "valid_files": self.valid_files,
            "invalid_files": self.invalid_files,
            "corrected_files": self.corrected_files,
            "failed_corrections": self.failed_corrections,
            "skipped_files": self.skipped_files,
            "scan_duration": self.scan_duration,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "success_rate": self.get_success_rate(),
            "correction_rate": self.get_correction_rate(),
        }