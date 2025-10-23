"""
Integration tests for SPDX Scanner.
"""

import pytest
import tempfile
from pathlib import Path

from spdx_scanner.scanner import create_default_scanner
from spdx_scanner.parser import create_default_parser
from spdx_scanner.validator import create_default_validator
from spdx_scanner.corrector import create_default_corrector
from spdx_scanner.reporter import create_default_reporter
from spdx_scanner.config import create_default_config_manager


class TestSPDXScannerIntegration:
    """Integration tests for the complete SPDX scanner workflow."""

    def test_complete_scan_workflow(self):
        """Test complete scan workflow with valid and invalid files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test files
            # Valid file with SPDX
            valid_file = temp_path / "valid.py"
            valid_file.write_text("""# SPDX-License-Identifier: MIT
# Copyright (c) 2023 Example Corp
# Example Project

print("Hello, world!")
""")

            # Invalid file without SPDX
            invalid_file = temp_path / "invalid.py"
            invalid_file.write_text("""print("Hello, world!")
""")

            # Invalid file with wrong SPDX
            wrong_file = temp_path / "wrong.py"
            wrong_file.write_text("""# SPDX-License-Identifier: INVALID-LICENSE
# Copyright (c) 2023 Example Corp

print("Hello, world!")
""")

            # Create scanner and scan files
            scanner = create_default_scanner()
            parser = create_default_parser()
            validator = create_default_validator()

            results = []
            for file_info in scanner.scan_directory(temp_path):
                # Parse SPDX information
                spdx_info = parser.parse_file(file_info)
                file_info.spdx_info = spdx_info

                # Validate SPDX information
                validation_result = validator.validate(spdx_info)

                # Create scan result
                from spdx_scanner.models import ScanResult
                scan_result = ScanResult(
                    file_info=file_info,
                    validation_result=validation_result,
                )
                results.append(scan_result)

            # Verify results
            assert len(results) == 3

            # Check valid file
            valid_result = next(r for r in results if r.file_info.filepath.name == "valid.py")
            assert valid_result.is_valid() is True
            assert valid_result.file_info.spdx_info.license_identifier == "MIT"

            # Check invalid file (missing SPDX)
            invalid_result = next(r for r in results if r.file_info.filepath.name == "invalid.py")
            assert invalid_result.is_valid() is False
            assert invalid_result.file_info.spdx_info.license_identifier is None

            # Check wrong file (invalid license)
            wrong_result = next(r for r in results if r.file_info.filepath.name == "wrong.py")
            assert wrong_result.is_valid() is False
            assert wrong_result.file_info.spdx_info.license_identifier == "INVALID-LICENSE"

    def test_correction_workflow(self):
        """Test correction workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create file without SPDX
            test_file = temp_path / "test.py"
            original_content = """print("Hello, world!")
"""
            test_file.write_text(original_content)

            # Scan and parse
            scanner = create_default_scanner()
            parser = create_default_parser()
            corrector = create_default_corrector()

            file_info = None
            for fi in scanner.scan_directory(temp_path):
                spdx_info = parser.parse_file(fi)
                fi.spdx_info = spdx_info
                file_info = fi
                break

            assert file_info is not None
            assert file_info.needs_spdx_correction() is True

            # Correct the file
            result = corrector.correct_file(file_info, dry_run=False)

            assert result.success is True
            assert result.has_changes() is True
            assert result.backup_created is True

            # Verify the corrected content
            corrected_content = test_file.read_text()
            assert "SPDX-License-Identifier: MIT" in corrected_content
            assert "Copyright (c)" in corrected_content
            assert corrected_content != original_content

            # Verify backup was created
            backup_files = list(temp_path.glob("*.spdx-backup"))
            assert len(backup_files) == 1
            backup_content = backup_files[0].read_text()
            assert backup_content == original_content

    def test_dry_run_correction(self):
        """Test dry run correction."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create file without SPDX
            test_file = temp_path / "test.py"
            original_content = """print("Hello, world!")
"""
            test_file.write_text(original_content)

            # Scan and parse
            scanner = create_default_scanner()
            parser = create_default_parser()
            corrector = create_default_corrector()

            file_info = None
            for fi in scanner.scan_directory(temp_path):
                spdx_info = parser.parse_file(fi)
                fi.spdx_info = spdx_info
                file_info = fi
                break

            # Correct with dry run
            result = corrector.correct_file(file_info, dry_run=True)

            assert result.success is True
            assert result.has_changes() is True
            assert "dry run" in result.changes_made[0]

            # File should not be modified in dry run
            current_content = test_file.read_text()
            assert current_content == original_content

            # No backup should be created in dry run
            backup_files = list(temp_path.glob("*.spdx-backup"))
            assert len(backup_files) == 0

    def test_report_generation(self):
        """Test report generation in different formats."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test files
            valid_file = temp_path / "valid.py"
            valid_file.write_text("""# SPDX-License-Identifier: MIT
# Copyright (c) 2023 Example Corp

print("Hello, world!")
""")

            invalid_file = temp_path / "invalid.py"
            invalid_file.write_text("""print("Hello, world!")
""")

            # Scan and validate
            scanner = create_default_scanner()
            parser = create_default_parser()
            validator = create_default_validator()
            reporter = create_default_reporter()

            results = []
            for file_info in scanner.scan_directory(temp_path):
                spdx_info = parser.parse_file(file_info)
                file_info.spdx_info = spdx_info
                validation_result = validator.validate(spdx_info)

                from spdx_scanner.models import ScanResult
                scan_result = ScanResult(
                    file_info=file_info,
                    validation_result=validation_result,
                )
                results.append(scan_result)

            # Generate reports in different formats
            formats = ["text", "json", "markdown", "csv"]

            for format in formats:
                report_file = temp_path / f"report.{format}"
                if format == "markdown":
                    report_file = temp_path / "report.md"
                elif format == "text":
                    report_file = temp_path / "report.txt"

                report_path = reporter.generate_report(
                    results,
                    reporter.create_summary(results),
                    format=format,
                    output_file=str(report_file)
                )

                assert report_path is not None
                assert Path(report_path).exists()
                assert Path(report_path).stat().st_size > 0

                # Verify content based on format
                content = Path(report_path).read_text()
                assert "SPDX" in content or "spdx" in content.lower()
                assert "valid.py" in content
                assert "invalid.py" in content

    def test_configuration_workflow(self):
        """Test configuration loading and usage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create configuration file
            config_file = temp_path / "spdx-scanner.config.json"
            config_data = {
                "project_name": "Test Project",
                "copyright_holder": "Test Corp",
                "default_license": "Apache-2.0",
                "validation_rules": {
                    "require_license_identifier": True,
                    "require_copyright": True,
                    "allow_unknown_licenses": False,
                },
                "correction_settings": {
                    "create_backups": True,
                    "default_license": "Apache-2.0",
                }
            }

            with open(config_file, 'w') as f:
                import json
                json.dump(config_data, f)

            # Load configuration
            config_manager = create_default_config_manager(config_file)
            config = config_manager.load_config()

            assert config.project_name == "Test Project"
            assert config.copyright_holder == "Test Corp"
            assert config.default_license == "Apache-2.0"
            assert config.validation_rules.require_license_identifier is True
            assert config.validation_rules.allow_unknown_licenses is False
            assert config.correction_settings.default_license == "Apache-2.0"

            # Test configuration with scanner
            from spdx_scanner.scanner import FileScanner
            scanner = FileScanner()
            # Configuration should be applied when creating other components

    def test_exclude_patterns(self):
        """Test file exclusion patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create files
            main_file = temp_path / "main.py"
            main_file.write_text("print('main')")

            test_file = temp_path / "test_main.py"
            test_file.write_text("print('test')")

            node_modules = temp_path / "node_modules"
            node_modules.mkdir()
            package_file = node_modules / "package.js"
            package_file.write_text("console.log('package');")

            # Scan with exclude patterns
            scanner = FileScanner(
                include_patterns=["**/*.py", "**/*.js"],
                exclude_patterns=["**/test_*", "**/node_modules/**"]
            )

            results = list(scanner.scan_directory(temp_path))
            file_paths = [str(r.filepath.relative_to(temp_path)) for r in results]

            # Should include main.py
            assert "main.py" in file_paths

            # Should exclude test files and node_modules
            assert "test_main.py" not in file_paths
            assert "node_modules/package.js" not in file_paths

    def test_binary_file_handling(self):
        """Test handling of binary files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create binary file
            binary_file = temp_path / "binary.bin"
            binary_file.write_bytes(b'\x00\x01\x02\x03\x04\x05')

            # Create text file
            text_file = temp_path / "text.py"
            text_file.write_text("print('hello')")

            # Scan files
            scanner = create_default_scanner()
            results = list(scanner.scan_directory(temp_path))

            # Should only find the text file
            assert len(results) == 1
            assert results[0].filepath.name == "text.py"

    def test_large_file_handling(self):
        """Test handling of large files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create large file
            large_file = temp_path / "large.py"
            large_file.write_text("x" * 100000)  # 100KB

            # Create normal file
            normal_file = temp_path / "normal.py"
            normal_file.write_text("print('hello')")

            # Scan with small file size limit
            scanner = FileScanner(max_file_size=1000)  # 1KB limit
            results = list(scanner.scan_directory(temp_path))

            # Should only find the normal file
            assert len(results) == 1
            assert results[0].filepath.name == "normal.py"

    def test_language_detection(self):
        """Test programming language detection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create files with different extensions
            files_and_languages = [
                ("test.py", "python"),
                ("test.js", "javascript"),
                ("test.java", "java"),
                ("test.c", "c"),
                ("test.cpp", "cpp"),
                ("test.go", "go"),
                ("test.rs", "rust"),
                ("test.html", "html"),
                ("test.css", "css"),
                ("test.sh", "shell"),
            ]

            for filename, expected_lang in files_and_languages:
                file_path = temp_path / filename
                file_path.write_text("# Test content\nprint('hello')")

            # Scan and check language detection
            scanner = create_default_scanner()
            results = list(scanner.scan_directory(temp_path))

            detected_languages = {r.filepath.name: r.language for r in results}

            for filename, expected_lang in files_and_languages:
                assert detected_languages[filename] == expected_lang


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_nonexistent_directory(self):
        """Test scanning non-existent directory."""
        scanner = create_default_scanner()

        with pytest.raises(FileNotFoundError):
            list(scanner.scan_directory(Path("/nonexistent/directory")))

    def test_permission_denied_file(self):
        """Test handling permission-denied files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create file and make it unreadable (if possible)
            test_file = temp_path / "readonly.py"
            test_file.write_text("print('hello')")

            try:
                # Try to make file unreadable (may not work on all systems)
                test_file.chmod(0o000)

                scanner = create_default_scanner()
                results = list(scanner.scan_directory(temp_path))

                # Should handle gracefully - either skip or include with error
                # The exact behavior depends on the system
                assert len(results) >= 0  # Should not crash

            finally:
                # Restore permissions for cleanup
                try:
                    test_file.chmod(0o644)
                except:
                    pass

    def test_malformed_configuration_file(self):
        """Test handling malformed configuration files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create malformed JSON file
            config_file = temp_path / "spdx-scanner.config.json"
            config_file.write_text("{ invalid json content")

            config_manager = create_default_config_manager(config_file)

            # Should handle gracefully and use defaults
            config = config_manager.load_config()
            assert isinstance(config, Configuration)
            assert config.project_name == "Unknown Project"  # Default value