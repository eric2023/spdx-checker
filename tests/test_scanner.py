"""
Tests for SPDX Scanner file scanner component.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from spdx_scanner.scanner import FileScanner, LanguageDetector, EncodingDetector, create_default_scanner
from spdx_scanner.models import FileInfo, SPDXInfo


class TestLanguageDetector:
    """Test language detection functionality."""

    def test_detect_language_by_extension(self):
        """Test language detection by file extension."""
        detector = LanguageDetector()

        # Test common extensions
        assert detector.detect_language(Path("test.py")) == "python"
        assert detector.detect_language(Path("test.js")) == "javascript"
        assert detector.detect_language(Path("test.ts")) == "typescript"
        assert detector.detect_language(Path("test.java")) == "java"
        assert detector.detect_language(Path("test.c")) == "c"
        assert detector.detect_language(Path("test.cpp")) == "cpp"
        assert detector.detect_language(Path("test.go")) == "go"
        assert detector.detect_language(Path("test.rs")) == "rust"
        assert detector.detect_language(Path("test.html")) == "html"
        assert detector.detect_language(Path("test.css")) == "css"

    def test_detect_language_unknown_extension(self):
        """Test language detection with unknown extension."""
        detector = LanguageDetector()
        assert detector.detect_language(Path("test.unknown")) == "unknown"
        assert detector.detect_language(Path("test")) == "unknown"

    def test_detect_language_case_insensitive(self):
        """Test language detection is case insensitive."""
        detector = LanguageDetector()
        assert detector.detect_language(Path("TEST.PY")) == "python"
        assert detector.detect_language(Path("Test.Js")) == "javascript"

    def test_detect_from_shebang(self):
        """Test language detection from shebang."""
        detector = LanguageDetector()

        content = "#!/usr/bin/env python\nprint('hello')"
        assert detector.detect_language(Path("script"), content) == "python"

        content = "#!/bin/bash\necho 'hello'"
        assert detector.detect_language(Path("script"), content) == "shell"

        content = "#!/usr/bin/perl\nprint 'hello';"
        assert detector.detect_language(Path("script"), content) == "perl"

    def test_is_source_file(self):
        """Test source file detection."""
        detector = LanguageDetector()

        assert detector.is_source_file(Path("test.py")) is True
        assert detector.is_source_file(Path("test.js")) is True
        assert detector.is_source_file(Path("test.txt")) is False
        assert detector.is_source_file(Path("test")) is False


class TestEncodingDetector:
    """Test encoding detection functionality."""

    def test_detect_encoding_utf8(self):
        """Test UTF-8 encoding detection."""
        detector = EncodingDetector()

        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as f:
            f.write("Hello, 世界! 🌍")
            temp_path = Path(f.name)

        try:
            encoding = detector.detect_encoding(temp_path)
            assert encoding == "utf-8"
        finally:
            temp_path.unlink()

    def test_detect_encoding_latin1(self):
        """Test Latin-1 encoding detection."""
        detector = EncodingDetector()

        with tempfile.NamedTemporaryFile(mode='w', encoding='latin-1', delete=False) as f:
            f.write("Hello, café!")
            temp_path = Path(f.name)

        try:
            encoding = detector.detect_encoding(temp_path)
            # Should detect as latin1 or similar
            assert encoding in ["ISO-8859-1", "WINDOWS-1252", "latin1"]
        finally:
            temp_path.unlink()

    def test_detect_line_endings(self):
        """Test line ending detection."""
        detector = EncodingDetector()

        assert detector.detect_line_endings("line1\nline2\n") == "\n"
        assert detector.detect_line_endings("line1\r\nline2\r\n") == "\r\n"
        assert detector.detect_line_endings("line1\rline2\r") == "\r"

    def test_has_shebang(self):
        """Test shebang detection."""
        detector = EncodingDetector()

        assert detector.has_shebang("#!/usr/bin/env python\nprint('hello')") is True
        assert detector.has_shebang("#!/bin/bash\necho 'hello'") is True
        assert detector.has_shebang("print('hello')") is False
        assert detector.has_shebang("# Not a shebang\nprint('hello')") is False

    def test_is_binary_content(self):
        """Test binary content detection."""
        detector = EncodingDetector()

        assert detector.is_binary_content("Hello, world!") is False
        assert detector.is_binary_content("print('hello')\n# Comment") is False
        assert detector.is_binary_content("Text with émojis 🌍") is False

        # Binary-like content (high ratio of non-printable chars)
        binary_like = "A" * 50 + "\x00\x01\x02\x03" * 50
        assert detector.is_binary_content(binary_like) is True


class TestFileScanner:
    """Test file scanner functionality."""

    def test_scanner_initialization(self):
        """Test scanner initialization."""
        scanner = FileScanner(
            include_patterns=["**/*.py"],
            exclude_patterns=["**/test_*"],
            follow_symlinks=True,
            max_file_size=1024 * 1024
        )

        assert scanner.include_patterns == ["**/*.py"]
        assert scanner.exclude_patterns == ["**/test_*"]
        assert scanner.follow_symlinks is True
        assert scanner.max_file_size == 1024 * 1024

    def test_scan_empty_directory(self):
        """Test scanning empty directory."""
        scanner = FileScanner()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            results = list(scanner.scan_directory(temp_path))
            assert len(results) == 0

    def test_scan_directory_with_files(self):
        """Test scanning directory with files."""
        scanner = FileScanner()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test files
            (temp_path / "test1.py").write_text("print('hello')")
            (temp_path / "test2.js").write_text("console.log('hello');")
            (temp_path / "test3.txt").write_text("Not source code")

            results = list(scanner.scan_directory(temp_path))

            # Should find Python and JavaScript files
            file_paths = [r.filepath.name for r in results]
            assert "test1.py" in file_paths
            assert "test2.js" in file_paths
            assert "test3.txt" not in file_paths  # Not a source file

    def test_scan_file(self):
        """Test scanning individual file."""
        scanner = FileScanner()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("print('hello world')\n# This is a test")
            temp_path = Path(f.name)

        try:
            file_info = scanner.scan_file(temp_path)
            assert file_info is not None
            assert file_info.filepath == temp_path
            assert file_info.language == "python"
            assert file_info.content == "print('hello world')\n# This is a test"
            assert file_info.encoding == "utf-8"
            assert file_info.has_shebang is False
            assert file_info.is_binary is False
            assert file_info.is_empty is False

        finally:
            temp_path.unlink()

    def test_scan_file_with_shebang(self):
        """Test scanning file with shebang."""
        scanner = FileScanner()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("#!/usr/bin/env python\nprint('hello world')")
            temp_path = Path(f.name)

        try:
            file_info = scanner.scan_file(temp_path)
            assert file_info is not None
            assert file_info.has_shebang is True
            assert file_info.content.startswith("#!/usr/bin/env python")

        finally:
            temp_path.unlink()

    def test_scan_binary_file(self):
        """Test scanning binary file."""
        scanner = FileScanner()

        # Create a binary file
        with tempfile.NamedTemporaryFile(suffix='.exe', delete=False) as f:
            f.write(b'\x00\x01\x02\x03\x04\x05')  # Binary content
            temp_path = Path(f.name)

        try:
            file_info = scanner.scan_file(temp_path)
            # Binary files should be skipped
            assert file_info is None

        finally:
            temp_path.unlink()

    def test_scan_large_file(self):
        """Test scanning large file."""
        scanner = FileScanner(max_file_size=100)  # 100 bytes max

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("x" * 200)  # 200 bytes
            temp_path = Path(f.name)

        try:
            file_info = scanner.scan_file(temp_path)
            # Large files should be skipped
            assert file_info is None

        finally:
            temp_path.unlink()

    def test_include_exclude_patterns(self):
        """Test include/exclude patterns."""
        scanner = FileScanner(
            include_patterns=["**/*.py", "**/*.js"],
            exclude_patterns=["**/test_*", "**/node_modules/**"]
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test files
            (temp_path / "main.py").write_text("print('main')")
            (temp_path / "test_main.py").write_text("print('test')")
            (temp_path / "utils.js").write_text("console.log('utils');")
            (temp_path / "README.md").write_text("# README")

            # Create subdirectory
            subdir = temp_path / "node_modules"
            subdir.mkdir()
            (subdir / "package.js").write_text("// package")

            results = list(scanner.scan_directory(temp_path))
            file_paths = [str(r.filepath.relative_to(temp_path)) for r in results]

            # Should include main.py and utils.js
            assert "main.py" in file_paths
            assert "utils.js" in file_paths

            # Should exclude test files and node_modules
            assert "test_main.py" not in file_paths
            assert "README.md" not in file_paths  # Not in include patterns
            assert "node_modules/package.js" not in file_paths

    def test_get_supported_languages(self):
        """Test getting supported languages."""
        scanner = FileScanner()
        languages = scanner.get_supported_languages()

        assert "python" in languages
        assert "javascript" in languages
        assert "java" in languages
        assert "c" in languages
        assert "cpp" in languages

    def test_is_language_supported(self):
        """Test language support checking."""
        scanner = FileScanner()

        assert scanner.is_language_supported("python") is True
        assert scanner.is_language_supported("javascript") is True
        assert scanner.is_language_supported("unknown") is False


class TestCreateDefaultScanner:
    """Test default scanner creation."""

    def test_create_default_scanner(self):
        """Test creating default scanner."""
        scanner = create_default_scanner()

        assert isinstance(scanner, FileScanner)
        assert len(scanner.include_patterns) > 0
        assert len(scanner.exclude_patterns) > 0
        assert scanner.follow_symlinks is False
        assert scanner.max_file_size == 10 * 1024 * 1024  # 10MB

    def test_default_include_patterns(self):
        """Test default include patterns."""
        scanner = create_default_scanner()

        # Should include common source file patterns
        assert "**/*.py" in scanner.include_patterns
        assert "**/*.js" in scanner.include_patterns
        assert "**/*.java" in scanner.include_patterns
        assert "**/*.c" in scanner.include_patterns
        assert "**/*.cpp" in scanner.include_patterns

    def test_default_exclude_patterns(self):
        """Test default exclude patterns."""
        scanner = create_default_scanner()

        # Should exclude common build/dependency directories
        assert "**/node_modules/**" in scanner.exclude_patterns
        assert "**/build/**" in scanner.exclude_patterns
        assert "**/dist/**" in scanner.exclude_patterns
        assert "**/.git/**" in scanner.exclude_patterns
        assert "**/__pycache__/**" in scanner.exclude_patterns

    def test_custom_patterns(self):
        """Test creating scanner with custom patterns."""
        include_patterns = ["**/*.py", "**/*.js"]
        exclude_patterns = ["**/test_*"]

        scanner = create_default_scanner(
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns
        )

        assert scanner.include_patterns == include_patterns
        assert scanner.exclude_patterns == exclude_patterns