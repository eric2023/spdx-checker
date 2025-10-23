"""
Tests for SPDX Scanner reporter component.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock

from spdx_scanner.reporter import (
    TextReportGenerator,
    JSONReportGenerator,
    HTMLReportGenerator,
    MarkdownReportGenerator,
    CSVReportGenerator,
    Reporter,
    create_default_reporter,
)
from spdx_scanner.models import ScanResult, ScanSummary, FileInfo, SPDXInfo, ValidationResult, ValidationError, ValidationSeverity


class TestTextReportGenerator:
    """Test text report generator."""

    def test_generate_empty_report(self):
        """Test generating empty text report."""
        generator = TextReportGenerator()
        results = []
        summary = ScanSummary()

        import io
        output = io.StringIO()
        generator.generate(results, summary, output)

        report = output.getvalue()
        assert "SPDX License Scanner Report" in report
        assert "Total Files Scanned: 0" in report
        assert "No files were scanned" in report

    def test_generate_report_with_results(self):
        """Test generating text report with results."""
        generator = TextReportGenerator()

        # Create test results
        file_info = FileInfo(
            filepath=Path("test.py"),
            language="python",
            content="print('hello')"
        )
        file_info.spdx_info = SPDXInfo(license_identifier="MIT")

        validation_result = ValidationResult(is_valid=True)
        result = ScanResult(file_info=file_info, validation_result=validation_result)

        results = [result]
        summary = ScanSummary()
        summary.total_files = 1
        summary.valid_files = 1
        summary.invalid_files = 0

        import io
        output = io.StringIO()
        generator.generate(results, summary, output)

        report = output.getvalue()
        assert "SPDX License Scanner Report" in report
        assert "Total Files Scanned: 1" in report
        assert "Valid Files: 1" in report

    def test_generate_report_with_invalid_files(self):
        """Test generating text report with invalid files."""
        generator = TextReportGenerator()

        # Create test results with invalid file
        file_info = FileInfo(
            filepath=Path("invalid.py"),
            language="python",
            content="print('hello')"
        )

        validation_result = ValidationResult(is_valid=False)
        validation_result.add_error(ValidationError(
            severity=ValidationSeverity.ERROR,
            message="Missing license identifier"
        ))

        result = ScanResult(file_info=file_info, validation_result=validation_result)

        results = [result]
        summary = ScanSummary()
        summary.total_files = 1
        summary.valid_files = 0
        summary.invalid_files = 1

        import io
        output = io.StringIO()
        generator.generate(results, summary, output)

        report = output.getvalue()
        assert "INVALID FILES" in report
        assert "invalid.py" in report
        assert "Missing license identifier" in report

    def test_get_file_extension(self):
        """Test getting file extension."""
        generator = TextReportGenerator()
        assert generator.get_file_extension() == ".txt"


class TestJSONReportGenerator:
    """Test JSON report generator."""

    def test_generate_json_report(self):
        """Test generating JSON report."""
        generator = JSONReportGenerator()

        # Create test results
        file_info = FileInfo(
            filepath=Path("test.py"),
            language="python",
            content="print('hello')"
        )
        file_info.spdx_info = SPDXInfo(license_identifier="MIT")

        validation_result = ValidationResult(is_valid=True)
        result = ScanResult(file_info=file_info, validation_result=validation_result)

        results = [result]
        summary = ScanSummary()
        summary.total_files = 1
        summary.valid_files = 1

        import io
        output = io.StringIO()
        generator.generate(results, summary, output)

        import json
        report_data = json.loads(output.getvalue())

        assert "metadata" in report_data
        assert "summary" in report_data
        assert "results" in report_data
        assert report_data["metadata"]["format"] == "json"
        assert report_data["metadata"]["generator"] == "SPDX Scanner"
        assert len(report_data["results"]) == 1

    def test_get_file_extension(self):
        """Test getting file extension."""
        generator = JSONReportGenerator()
        assert generator.get_file_extension() == ".json"


class TestHTMLReportGenerator:
    """Test HTML report generator."""

    def test_generate_html_report(self):
        """Test generating HTML report."""
        generator = HTMLReportGenerator()

        # Create test results
        file_info = FileInfo(
            filepath=Path("test.py"),
            language="python",
            content="print('hello')"
        )
        file_info.spdx_info = SPDXInfo(license_identifier="MIT")

        validation_result = ValidationResult(is_valid=True)
        result = ScanResult(file_info=file_info, validation_result=validation_result)

        results = [result]
        summary = ScanSummary()
        summary.total_files = 1
        summary.valid_files = 1

        import io
        output = io.StringIO()
        generator.generate(results, summary, output)

        report = output.getvalue()
        assert "<!DOCTYPE html>" in report
        assert "SPDX License Scanner Report" in report
        assert "test.py" in report
        assert "python" in report
        assert "MIT" in report

    def test_get_file_extension(self):
        """Test getting file extension."""
        generator = HTMLReportGenerator()
        assert generator.get_file_extension() == ".html"


class TestMarkdownReportGenerator:
    """Test Markdown report generator."""

    def test_generate_markdown_report(self):
        """Test generating Markdown report."""
        generator = MarkdownReportGenerator()

        # Create test results
        file_info = FileInfo(
            filepath=Path("test.py"),
            language="python",
            content="print('hello')"
        )
        file_info.spdx_info = SPDXInfo(license_identifier="MIT")

        validation_result = ValidationResult(is_valid=True)
        result = ScanResult(file_info=file_info, validation_result=validation_result)

        results = [result]
        summary = ScanSummary()
        summary.total_files = 1
        summary.valid_files = 1

        import io
        output = io.StringIO()
        generator.generate(results, summary, output)

        report = output.getvalue()
        assert "# SPDX License Scanner Report" in report
        assert "## Summary" in report
        assert "- **Total Files:** 1" in report
        assert "- **Valid Files:** 1" in report
        assert "`test.py`" in report

    def test_get_file_extension(self):
        """Test getting file extension."""
        generator = MarkdownReportGenerator()
        assert generator.get_file_extension() == ".md"


class TestCSVReportGenerator:
    """Test CSV report generator."""

    def test_generate_csv_report(self):
        """Test generating CSV report."""
        generator = CSVReportGenerator()

        # Create test results
        file_info = FileInfo(
            filepath=Path("test.py"),
            language="python",
            content="print('hello')"
        )
        file_info.spdx_info = SPDXInfo(license_identifier="MIT")

        validation_result = ValidationResult(is_valid=True)
        result = ScanResult(file_info=file_info, validation_result=validation_result)
        result.scan_time = 0.123

        results = [result]
        summary = ScanSummary()

        import io
        output = io.StringIO()
        generator.generate(results, summary, output)

        report = output.getvalue()
        lines = report.strip().split('\n')

        # Check header
        assert "File Path" in lines[0]
        assert "Language" in lines[0]
        assert "License" in lines[0]
        assert "Valid" in lines[0]

        # Check data row
        data_row = lines[1]
        assert "test.py" in data_row
        assert "python" in data_row
        assert "MIT" in data_row
        assert "Yes" in data_row
        assert "0.123" in data_row

    def test_get_file_extension(self):
        """Test getting file extension."""
        generator = CSVReportGenerator()
        assert generator.get_file_extension() == ".csv"


class TestReporter:
    """Test main reporter class."""

    def test_reporter_initialization(self):
        """Test reporter initialization."""
        reporter = Reporter()
        assert len(reporter.generators) == 5
        assert "text" in reporter.generators
        assert "json" in reporter.generators
        assert "html" in reporter.generators
        assert "markdown" in reporter.generators
        assert "csv" in reporter.generators

    def test_generate_report_text_format(self):
        """Test generating report in text format."""
        reporter = Reporter()

        # Create test results
        file_info = FileInfo(
            filepath=Path("test.py"),
            language="python",
            content="print('hello')"
        )
        file_info.spdx_info = SPDXInfo(license_identifier="MIT")

        validation_result = ValidationResult(is_valid=True)
        result = ScanResult(file_info=file_info, validation_result=validation_result)

        results = [result]
        summary = ScanSummary()
        summary.total_files = 1
        summary.valid_files = 1

        report_content = reporter.generate_report(results, summary, format="text")

        assert "SPDX License Scanner Report" in report_content
        assert "Total Files Scanned: 1" in report_content

    def test_generate_report_to_file(self):
        """Test generating report to file."""
        reporter = Reporter()

        # Create test results
        file_info = FileInfo(
            filepath=Path("test.py"),
            language="python",
            content="print('hello')"
        )
        file_info.spdx_info = SPDXInfo(license_identifier="MIT")

        validation_result = ValidationResult(is_valid=True)
        result = ScanResult(file_info=file_info, validation_result=validation_result)

        results = [result]
        summary = ScanSummary()
        summary.total_files = 1
        summary.valid_files = 1

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            temp_path = Path(f.name)

        try:
            report_path = reporter.generate_report(results, summary, format="text", output_file=str(temp_path))

            assert report_path == str(temp_path)
            assert temp_path.exists()

            content = temp_path.read_text()
            assert "SPDX License Scanner Report" in content
            assert "Total Files Scanned: 1" in content

        finally:
            temp_path.unlink()

    def test_get_supported_formats(self):
        """Test getting supported formats."""
        reporter = Reporter()
        formats = reporter.get_supported_formats()

        assert "text" in formats
        assert "json" in formats
        assert "html" in formats
        assert "markdown" in formats
        assert "csv" in formats
        assert len(formats) == 5

    def test_get_file_extension(self):
        """Test getting file extension for format."""
        reporter = Reporter()

        assert reporter.get_file_extension("text") == ".txt"
        assert reporter.get_file_extension("json") == ".json"
        assert reporter.get_file_extension("html") == ".html"
        assert reporter.get_file_extension("markdown") == ".md"
        assert reporter.get_file_extension("csv") == ".csv"

    def test_unsupported_format(self):
        """Test error with unsupported format."""
        reporter = Reporter()

        with pytest.raises(ValueError, match="Unsupported report format"):
            reporter.generate_report([], ScanSummary(), format="unsupported")

    def test_create_summary(self):
        """Test creating summary from results."""
        reporter = Reporter()

        # Create test results
        file_info1 = FileInfo(filepath=Path("valid.py"), language="python", content="valid")
        file_info1.spdx_info = SPDXInfo(license_identifier="MIT")
        validation_result1 = ValidationResult(is_valid=True)
        result1 = ScanResult(file_info=file_info1, validation_result=validation_result1)

        file_info2 = FileInfo(filepath=Path("invalid.py"), language="python", content="invalid")
        validation_result2 = ValidationResult(is_valid=False)
        result2 = ScanResult(file_info=file_info2, validation_result=validation_result2)

        results = [result1, result2]
        summary = reporter.create_summary(results)

        assert summary.total_files == 2
        assert summary.valid_files == 1
        assert summary.invalid_files == 1
        assert summary.start_time is not None
        assert summary.end_time is not None
        assert summary.scan_duration is not None


class TestCreateDefaultReporter:
    """Test default reporter creation."""

    def test_create_default_reporter(self):
        """Test creating default reporter."""
        reporter = create_default_reporter()
        assert isinstance(reporter, Reporter)
        assert len(reporter.generators) == 5