"""
Reporting and output system for SPDX Scanner.

This module provides functionality to generate reports in various formats
(JSON, HTML, Markdown, plain text, CSV) with detailed statistics and findings.
"""

import csv
import json
import html
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, TextIO
import logging

from .models import FileInfo, ScanResult, ScanSummary, ValidationSeverity


logger = logging.getLogger(__name__)


class ReportGenerator:
    """Base class for report generators."""

    def generate(self, results: List[ScanResult], summary: ScanSummary, output: TextIO) -> None:
        """Generate report and write to output."""
        raise NotImplementedError("Subclasses must implement generate method")

    def get_file_extension(self) -> str:
        """Get the file extension for this report format."""
        raise NotImplementedError("Subclasses must implement get_file_extension method")


class TextReportGenerator(ReportGenerator):
    """Plain text report generator."""

    def generate(self, results: List[ScanResult], summary: ScanSummary, output: TextIO) -> None:
        """Generate plain text report."""
        self._write_header(output, summary)
        self._write_summary(output, summary)
        self._write_details(output, results)
        self._write_footer(output, summary)

    def get_file_extension(self) -> str:
        return ".txt"

    def _write_header(self, output: TextIO, summary: ScanSummary) -> None:
        """Write report header."""
        output.write("=" * 80 + "\n")
        output.write("SPDX License Scanner Report\n")
        output.write("=" * 80 + "\n")
        output.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        if summary.start_time:
            output.write(f"Scan Duration: {summary.scan_duration:.2f}s\n")
        output.write("\n")

    def _write_summary(self, output: TextIO, summary: ScanSummary) -> None:
        """Write summary section."""
        output.write("SUMMARY\n")
        output.write("-" * 40 + "\n")
        output.write(f"Total Files Scanned: {summary.total_files}\n")
        output.write(f"Valid Files: {summary.valid_files} ({summary.get_success_rate():.1f}%)\n")
        output.write(f"Invalid Files: {summary.invalid_files}\n")
        output.write(f"Files Corrected: {summary.corrected_files}\n")
        output.write(f"Failed Corrections: {summary.failed_corrections}\n")
        output.write(f"Skipped Files: {summary.skipped_files}\n")
        output.write("\n")

    def _write_details(self, output: TextIO, results: List[ScanResult]) -> None:
        """Write detailed results."""
        if not results:
            output.write("No files were scanned.\n")
            return

        # Group results by status
        invalid_results = [r for r in results if not r.is_valid()]
        corrected_results = [r for r in results if r.was_corrected()]
        failed_results = [r for r in results if r.correction_result and not r.correction_result.success]

        if invalid_results:
            output.write("INVALID FILES\n")
            output.write("-" * 40 + "\n")
            for result in invalid_results:
                self._write_file_result(output, result)
            output.write("\n")

        if corrected_results:
            output.write("CORRECTED FILES\n")
            output.write("-" * 40 + "\n")
            for result in corrected_results:
                self._write_file_result(output, result, show_corrections=True)
            output.write("\n")

        if failed_results:
            output.write("FAILED CORRECTIONS\n")
            output.write("-" * 40 + "\n")
            for result in failed_results:
                self._write_file_result(output, result, show_failures=True)
            output.write("\n")

    def _write_file_result(self, output: TextIO, result: ScanResult, show_corrections: bool = False, show_failures: bool = False) -> None:
        """Write individual file result."""
        file_path = result.file_info.filepath
        output.write(f"File: {file_path}\n")
        output.write(f"  Language: {result.file_info.language}\n")

        if result.file_info.spdx_info and result.file_info.spdx_info.license_identifier:
            output.write(f"  License: {result.file_info.spdx_info.license_identifier}\n")

        # Write validation errors
        if result.validation_result.errors:
            output.write("  Validation Errors:\n")
            for error in result.validation_result.errors:
                output.write(f"    - {error.message}\n")
                if error.suggestion:
                    output.write(f"      Suggestion: {error.suggestion}\n")

        # Write validation warnings
        if result.validation_result.warnings:
            output.write("  Validation Warnings:\n")
            for warning in result.validation_result.warnings:
                output.write(f"    - {warning.message}\n")
                if warning.suggestion:
                    output.write(f"      Suggestion: {warning.suggestion}\n")

        # Write correction information
        if show_corrections and result.correction_result:
            output.write("  Corrections Made:\n")
            for change in result.correction_result.changes_made:
                output.write(f"    - {change}\n")
            if result.correction_result.backup_created:
                output.write(f"  Backup created: {result.correction_result.backup_path}\n")

        # Write failure information
        if show_failures and result.correction_result and not result.correction_result.success:
            output.write(f"  Correction failed: {result.correction_result.error_message}\n")

        output.write("\n")

    def _write_footer(self, output: TextIO, summary: ScanSummary) -> None:
        """Write report footer."""
        output.write("=" * 80 + "\n")
        output.write("End of Report\n")
        output.write("=" * 80 + "\n")


class JSONReportGenerator(ReportGenerator):
    """JSON report generator."""

    def generate(self, results: List[ScanResult], summary: ScanSummary, output: TextIO) -> None:
        """Generate JSON report."""
        report_data = {
            "metadata": {
                "generator": "SPDX Scanner",
                "version": "0.1.0",
                "generated_at": datetime.now().isoformat(),
                "format": "json",
            },
            "summary": summary.to_dict(),
            "results": [result.to_dict() for result in results],
        }

        json.dump(report_data, output, indent=2, ensure_ascii=False)

    def get_file_extension(self) -> str:
        return ".json"


class HTMLReportGenerator(ReportGenerator):
    """HTML report generator."""

    def generate(self, results: List[ScanResult], summary: ScanSummary, output: TextIO) -> None:
        """Generate HTML report."""
        self._write_html_header(output)
        self._write_html_summary(output, summary)
        self._write_html_details(output, results)
        self._write_html_footer(output)

    def get_file_extension(self) -> str:
        return ".html"

    def _write_html_header(self, output: TextIO) -> None:
        """Write HTML header."""
        output.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SPDX License Scanner Report</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { border-bottom: 2px solid #e0e0e0; padding-bottom: 20px; margin-bottom: 20px; }
        .summary { background: #f8f9fa; padding: 15px; border-radius: 6px; margin-bottom: 20px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .stat-card { background: white; padding: 15px; border-radius: 6px; border-left: 4px solid #007bff; }
        .stat-value { font-size: 24px; font-weight: bold; color: #007bff; }
        .stat-label { color: #666; font-size: 14px; }
        .file-result { margin-bottom: 15px; padding: 15px; border-radius: 6px; border: 1px solid #e0e0e0; }
        .file-result.valid { border-left: 4px solid #28a745; background: #f8fff8; }
        .file-result.invalid { border-left: 4px solid #dc3545; background: #fff8f8; }
        .file-result.corrected { border-left: 4px solid #ffc107; background: #fffbf0; }
        .error { color: #dc3545; }
        .warning { color: #ffc107; }
        .success { color: #28a745; }
        .code { font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace; background: #f8f8f8; padding: 2px 4px; border-radius: 3px; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #e0e0e0; }
        th { background: #f8f9fa; font-weight: 600; }
        .collapsible { cursor: pointer; }
        .content { display: none; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
""")

    def _write_html_summary(self, output: TextIO, summary: ScanSummary) -> None:
        """Write HTML summary section."""
        output.write(f"""
        <div class="header">
            <h1>SPDX License Scanner Report</h1>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            {f'<p>Scan Duration: {summary.scan_duration:.2f}s</p>' if summary.scan_duration else ''}
        </div>

        <div class="summary">
            <h2>Summary</h2>
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value">{summary.total_files}</div>
                    <div class="stat-label">Total Files</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{summary.valid_files}</div>
                    <div class="stat-label">Valid Files</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{summary.invalid_files}</div>
                    <div class="stat-label">Invalid Files</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{summary.corrected_files}</div>
                    <div class="stat-label">Corrected Files</div>
                </div>
            </div>
            <p>Success Rate: <strong>{summary.get_success_rate():.1f}%</strong></p>
            {f'<p>Correction Rate: <strong>{summary.get_correction_rate():.1f}%</strong></p>' if summary.invalid_files > 0 else ''}
        </div>
""")

    def _write_html_details(self, output: TextIO, results: List[ScanResult]) -> None:
        """Write HTML details section."""
        if not results:
            output.write("<p>No files were scanned.</p>")
            return

        # Group results
        invalid_results = [r for r in results if not r.is_valid()]
        corrected_results = [r for r in results if r.was_corrected()]

        output.write("<h2>Detailed Results</h2>")

        if invalid_results:
            output.write("""
        <h3>Invalid Files</h3>
        <table>
            <thead>
                <tr>
                    <th>File</th>
                    <th>Language</th>
                    <th>License</th>
                    <th>Issues</th>
                </tr>
            </thead>
            <tbody>
""")
            for result in invalid_results:
                self._write_html_file_row(output, result)
            output.write("</tbody></table>")

        if corrected_results:
            output.write("<h3>Corrected Files</h3>")
            for result in corrected_results:
                self._write_html_file_details(output, result)

    def _write_html_file_row(self, output: TextIO, result: ScanResult) -> None:
        """Write HTML table row for a file result."""
        file_path = html.escape(str(result.file_info.filepath))
        language = result.file_info.language
        license_id = result.file_info.spdx_info.license_identifier if result.file_info.spdx_info else "None"
        issues = len(result.validation_result.errors) + len(result.validation_result.warnings)

        output.write(f"""
            <tr>
                <td><code>{file_path}</code></td>
                <td>{language}</td>
                <td>{license_id}</td>
                <td>{issues}</td>
            </tr>
""")

    def _write_html_file_details(self, output: TextIO, result: ScanResult) -> None:
        """Write HTML details for a file result."""
        file_path = html.escape(str(result.file_info.filepath))
        output.write(f"""
        <div class="file-result corrected">
            <div class="collapsible" onclick="toggleContent(this)">
                <strong>{file_path}</strong> - {result.file_info.language}
            </div>
            <div class="content">
""")

        if result.validation_result.errors:
            output.write("<h4>Validation Errors</h4><ul>")
            for error in result.validation_result.errors:
                output.write(f"<li class='error'>{html.escape(error.message)}")
                if error.suggestion:
                    output.write(f" <em>Suggestion: {html.escape(error.suggestion)}</em>")
                output.write("</li>")
            output.write("</ul>")

        if result.correction_result and result.correction_result.changes_made:
            output.write("<h4>Changes Made</h4><ul>")
            for change in result.correction_result.changes_made:
                output.write(f"<li>{html.escape(change)}</li>")
            output.write("</ul>")

        output.write("</div></div>")

    def _write_html_footer(self, output: TextIO) -> None:
        """Write HTML footer."""
        output.write("""
    </div>
    <script>
        function toggleContent(element) {
            var content = element.nextElementSibling;
            if (content.style.display === "none" || content.style.display === "") {
                content.style.display = "block";
            } else {
                content.style.display = "none";
            }
        }
    </script>
</body>
</html>
""")


class MarkdownReportGenerator(ReportGenerator):
    """Markdown report generator."""

    def generate(self, results: List[ScanResult], summary: ScanSummary, output: TextIO) -> None:
        """Generate Markdown report."""
        self._write_header(output, summary)
        self._write_summary(output, summary)
        self._write_details(output, results)
        self._write_footer(output, summary)

    def get_file_extension(self) -> str:
        return ".md"

    def _write_header(self, output: TextIO, summary: ScanSummary) -> None:
        """Write Markdown header."""
        output.write("# SPDX License Scanner Report\n\n")
        output.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        if summary.scan_duration:
            output.write(f"**Scan Duration:** {summary.scan_duration:.2f}s\n")
        output.write("\n")

    def _write_summary(self, output: TextIO, summary: ScanSummary) -> None:
        """Write Markdown summary."""
        output.write("## Summary\n\n")
        output.write(f"- **Total Files:** {summary.total_files}\n")
        output.write(f"- **Valid Files:** {summary.valid_files} ({summary.get_success_rate():.1f}%)\n")
        output.write(f"- **Invalid Files:** {summary.invalid_files}\n")
        output.write(f"- **Corrected Files:** {summary.corrected_files}\n")
        output.write(f"- **Failed Corrections:** {summary.failed_corrections}\n")
        output.write(f"- **Skipped Files:** {summary.skipped_files}\n")
        output.write(f"- **Success Rate:** {summary.get_success_rate():.1f}%\n")
        if summary.invalid_files > 0:
            output.write(f"- **Correction Rate:** {summary.get_correction_rate():.1f}%\n")
        output.write("\n")

    def _write_details(self, output: TextIO, results: List[ScanResult]) -> None:
        """Write Markdown details."""
        if not results:
            output.write("No files were scanned.\n\n")
            return

        # Group results
        invalid_results = [r for r in results if not r.is_valid()]
        corrected_results = [r for r in results if r.was_corrected()]

        if invalid_results:
            output.write("## Invalid Files\n\n")
            output.write("| File | Language | License | Issues |\n")
            output.write("|------|----------|---------|--------|\n")
            for result in invalid_results:
                file_path = str(result.file_info.filepath)
                language = result.file_info.language
                license_id = result.file_info.spdx_info.license_identifier if result.file_info.spdx_info else "None"
                issues = len(result.validation_result.errors) + len(result.validation_result.warnings)
                output.write(f"| `{file_path}` | {language} | {license_id} | {issues} |\n")
            output.write("\n")

        if corrected_results:
            output.write("## Corrected Files\n\n")
            for result in corrected_results:
                self._write_file_details(output, result)

    def _write_file_details(self, output: TextIO, result: ScanResult) -> None:
        """Write Markdown details for a file result."""
        file_path = str(result.file_info.filepath)
        output.write(f"### {file_path}\n\n")
        output.write(f"- **Language:** {result.file_info.language}\n")

        if result.file_info.spdx_info and result.file_info.spdx_info.license_identifier:
            output.write(f"- **License:** {result.file_info.spdx_info.license_identifier}\n")

        if result.validation_result.errors:
            output.write("- **Validation Errors:**\n")
            for error in result.validation_result.errors:
                output.write(f"  - {error.message}\n")
                if error.suggestion:
                    output.write(f"    - *Suggestion: {error.suggestion}*\n")

        if result.correction_result and result.correction_result.changes_made:
            output.write("- **Changes Made:**\n")
            for change in result.correction_result.changes_made:
                output.write(f"  - {change}\n")

        output.write("\n")

    def _write_footer(self, output: TextIO, summary: ScanSummary) -> None:
        """Write Markdown footer."""
        output.write("---\n\n")
        output.write("*Generated by SPDX Scanner*\n")


class CSVReportGenerator(ReportGenerator):
    """CSV report generator."""

    def generate(self, results: List[ScanResult], summary: ScanSummary, output: TextIO) -> None:
        """Generate CSV report."""
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            "File Path", "Language", "License", "Valid", "Errors", "Warnings",
            "Corrected", "Backup Created", "Scan Time"
        ])

        # Write data rows
        for result in results:
            writer.writerow([
                str(result.file_info.filepath),
                result.file_info.language,
                result.file_info.spdx_info.license_identifier if result.file_info.spdx_info else "",
                "Yes" if result.is_valid() else "No",
                len(result.validation_result.errors),
                len(result.validation_result.warnings),
                "Yes" if result.was_corrected() else "No",
                "Yes" if result.correction_result and result.correction_result.backup_created else "No",
                f"{result.scan_time:.3f}" if result.scan_time else "",
            ])

    def get_file_extension(self) -> str:
        return ".csv"


class Reporter:
    """Main reporter class that coordinates report generation."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize reporter with configuration."""
        self.config = config or {}
        self.generators = {
            'text': TextReportGenerator(),
            'json': JSONReportGenerator(),
            'html': HTMLReportGenerator(),
            'markdown': MarkdownReportGenerator(),
            'csv': CSVReportGenerator(),
        }

    def generate_report(
        self,
        results: List[ScanResult],
        summary: ScanSummary,
        format: str = 'text',
        output_file: Optional[str] = None,
    ) -> Optional[str]:
        """Generate report in specified format."""
        if format not in self.generators:
            raise ValueError(f"Unsupported report format: {format}")

        generator = self.generators[format]

        if output_file:
            # Write to file
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    generator.generate(results, summary, f)
                logger.info(f"Report generated: {output_file}")
                return output_file
            except Exception as e:
                logger.error(f"Failed to generate report file {output_file}: {e}")
                raise
        else:
            # Return as string
            import io
            output = io.StringIO()
            generator.generate(results, summary, output)
            return output.getvalue()

    def get_supported_formats(self) -> List[str]:
        """Get list of supported report formats."""
        return list(self.generators.keys())

    def get_file_extension(self, format: str) -> str:
        """Get file extension for a specific format."""
        if format not in self.generators:
            raise ValueError(f"Unsupported report format: {format}")
        return self.generators[format].get_file_extension()

    def create_summary(self, results: List[ScanResult]) -> ScanSummary:
        """Create summary from scan results."""
        summary = ScanSummary()

        if not results:
            return summary

        # Set time information
        summary.start_time = datetime.now()
        summary.end_time = datetime.now()

        # Calculate summary statistics
        for result in results:
            summary.add_result(result)

        # Calculate duration
        if summary.start_time and summary.end_time:
            summary.scan_duration = (summary.end_time - summary.start_time).total_seconds()

        return summary


def create_default_reporter(config: Optional[Dict[str, Any]] = None) -> Reporter:
    """Create a default reporter instance."""
    return Reporter(config)