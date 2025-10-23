"""
File scanner component for SPDX Scanner.

This module provides functionality to discover and analyze source code files,
detect their programming language, encoding, and other metadata needed for
SPDX license declaration processing.
"""

import chardet
import mimetypes
from pathlib import Path
from typing import List, Optional, Set, Iterator, Dict, Any
import logging
from datetime import datetime

from .models import FileInfo, SPDXInfo


logger = logging.getLogger(__name__)


class LanguageDetector:
    """Detects programming language based on file extension and content."""

    # Language mappings by file extension
    LANGUAGE_EXTENSIONS = {
        # Python
        '.py': 'python',
        '.pyx': 'python',
        '.pyi': 'python',

        # JavaScript/TypeScript
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.mjs': 'javascript',

        # Java
        '.java': 'java',
        '.class': 'java',
        '.jar': 'java',

        # C/C++
        '.c': 'c',
        '.cpp': 'cpp',
        '.cxx': 'cpp',
        '.cc': 'cpp',
        '.h': 'c',
        '.hpp': 'cpp',
        '.hxx': 'cpp',

        # Go
        '.go': 'go',

        # Rust
        '.rs': 'rust',

        # Shell scripts
        '.sh': 'shell',
        '.bash': 'shell',
        '.zsh': 'shell',
        '.fish': 'shell',
        '.csh': 'shell',
        '.tcsh': 'shell',
        '.ksh': 'shell',

        # Web technologies
        '.html': 'html',
        '.htm': 'html',
        '.css': 'css',
        '.scss': 'scss',
        '.sass': 'sass',
        '.less': 'less',

        # Configuration files
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.toml': 'toml',
        '.xml': 'xml',

        # Other languages
        '.rb': 'ruby',
        '.php': 'php',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.r': 'r',
        '.m': 'objective-c',
        '.mm': 'objective-c',
        '.pl': 'perl',
        '.lua': 'lua',
        '.dart': 'dart',
        '.vue': 'vue',
        '.svelte': 'svelte',
    }

    # Shebang patterns for language detection
    SHEBANG_PATTERNS = {
        'python': [r'#!/.*python'],
        'javascript': [r'#!/.*node'],
        'shell': [r'#!/.*sh', r'#!/.*bash', r'#!/.*zsh', r'#!/.*fish'],
        'perl': [r'#!/.*perl'],
        'ruby': [r'#!/.*ruby'],
        'lua': [r'#!/.*lua'],
    }

    @classmethod
    def detect_language(cls, filepath: Path, content: Optional[str] = None) -> str:
        """Detect programming language from file extension and optionally content."""
        extension = filepath.suffix.lower()

        # First try extension-based detection
        if extension in cls.LANGUAGE_EXTENSIONS:
            return cls.LANGUAGE_EXTENSIONS[extension]

        # If no extension match and content is provided, try shebang detection
        if content:
            return cls._detect_from_shebang(content)

        # Default to unknown
        return 'unknown'

    @classmethod
    def _detect_from_shebang(cls, content: str) -> str:
        """Detect language from shebang line."""
        lines = content.split('\n', 3)  # Check first 3 lines
        for line in lines:
            line = line.strip()
            if line.startswith('#!'):
                for language, patterns in cls.SHEBANG_PATTERNS.items():
                    import re
                    for pattern in patterns:
                        if re.match(pattern, line, re.IGNORECASE):
                            return language
        return 'unknown'

    @classmethod
    def is_source_file(cls, filepath: Path) -> bool:
        """Check if file is likely a source code file."""
        extension = filepath.suffix.lower()
        return extension in cls.LANGUAGE_EXTENSIONS


class EncodingDetector:
    """Detects file encoding and line endings."""

    @staticmethod
    def detect_encoding(filepath: Path) -> str:
        """Detect file encoding using chardet."""
        try:
            # Read raw bytes
            with open(filepath, 'rb') as f:
                raw_data = f.read(10000)  # Read first 10KB

            if not raw_data:
                return 'utf-8'  # Default for empty files

            # Use chardet for detection
            result = chardet.detect(raw_data)
            encoding = result.get('encoding', 'utf-8')
            confidence = result.get('confidence', 0)

            # Only use detected encoding if confidence is high enough
            if encoding and confidence > 0.7:
                return encoding.lower()

            return 'utf-8'  # Fallback to UTF-8

        except Exception as e:
            logger.warning(f"Failed to detect encoding for {filepath}: {e}")
            return 'utf-8'

    @staticmethod
    def detect_line_endings(content: str) -> str:
        """Detect line ending style from content."""
        if '\r\n' in content:
            return '\r\n'  # Windows
        elif '\r' in content:
            return '\r'    # Old Mac
        else:
            return '\n'    # Unix/Linux

    @staticmethod
    def has_shebang(content: str) -> bool:
        """Check if content starts with a shebang line."""
        lines = content.split('\n', 1)
        return len(lines) > 0 and lines[0].strip().startswith('#!')

    @staticmethod
    def is_binary_content(content: str, sample_size: int = 1024) -> bool:
        """Check if content appears to be binary."""
        if not content:
            return False

        # Sample first part of content
        sample = content[:sample_size]

        # Check for null bytes (strong indicator of binary)
        if '\x00' in sample:
            return True

        # Check ratio of printable to non-printable characters
        printable_count = sum(1 for c in sample if c.isprintable() or c.isspace())
        total_count = len(sample)

        # If less than 90% printable characters, likely binary
        return (printable_count / total_count) < 0.9


class FileScanner:
    """Scans directories and files for SPDX license analysis."""

    def __init__(
        self,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        follow_symlinks: bool = False,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
    ):
        """Initialize file scanner with configuration."""
        self.include_patterns = include_patterns or ["**/*"]
        self.exclude_patterns = exclude_patterns or []
        self.follow_symlinks = follow_symlinks
        self.max_file_size = max_file_size
        self.language_detector = LanguageDetector()
        self.encoding_detector = EncodingDetector()

    def scan_directory(self, directory: Path) -> Iterator[FileInfo]:
        """Scan directory and yield FileInfo objects."""
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        if not directory.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")

        logger.info(f"Starting directory scan: {directory}")

        # Convert patterns to Path objects for matching
        from pathspec import PathSpec
        include_spec = PathSpec.from_lines("gitwildmatch", self.include_patterns)
        exclude_spec = PathSpec.from_lines("gitwildmatch", self.exclude_patterns)

        file_count = 0

        # Walk through directory
        for root, dirs, files in self._walk_directory(directory):
            # Filter out hidden directories and symlinks if needed
            if not self.follow_symlinks:
                dirs[:] = [d for d in dirs if not d.startswith('.')]

            for filename in files:
                filepath = Path(root) / filename

                # Skip hidden files and symlinks if needed
                if filename.startswith('.') or (not self.follow_symlinks and filepath.is_symlink()):
                    continue

                # Check file size
                try:
                    if filepath.stat().st_size > self.max_file_size:
                        logger.warning(f"Skipping large file: {filepath}")
                        continue
                except (OSError, FileNotFoundError):
                    continue

                # Check include/exclude patterns
                relative_path = filepath.relative_to(directory)

                if not include_spec.match_file(str(relative_path)):
                    continue

                if exclude_spec.match_file(str(relative_path)):
                    continue

                # Process file
                try:
                    file_info = self.scan_file(filepath)
                    if file_info:
                        yield file_info
                        file_count += 1

                        if file_count % 100 == 0:
                            logger.info(f"Scanned {file_count} files...")

                except Exception as e:
                    logger.error(f"Error scanning file {filepath}: {e}")
                    continue

        logger.info(f"Directory scan completed. Total files scanned: {file_count}")

    def scan_file(self, filepath: Path) -> Optional[FileInfo]:
        """Scan a single file and return FileInfo."""
        try:
            # Basic file checks
            if not filepath.exists():
                logger.warning(f"File not found: {filepath}")
                return None

            if not filepath.is_file():
                logger.warning(f"Not a regular file: {filepath}")
                return None

            # Skip binary files
            if self._is_likely_binary(filepath):
                logger.debug(f"Skipping binary file: {filepath}")
                return None

            # Detect encoding and read content
            encoding = self.encoding_detector.detect_encoding(filepath)

            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Try with UTF-8 with error handling
                with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()

            # Detect file properties
            language = self.language_detector.detect_language(filepath, content)
            line_endings = self.encoding_detector.detect_line_endings(content)
            has_shebang = self.encoding_detector.has_shebang(content)
            is_binary = self.encoding_detector.is_binary_content(content)
            is_empty = len(content.strip()) == 0

            # Get file stats
            try:
                stat = filepath.stat()
                size = stat.st_size
                last_modified = datetime.fromtimestamp(stat.st_mtime)
            except (OSError, FileNotFoundError):
                size = len(content.encode(encoding))
                last_modified = datetime.now()

            # Create SPDX info (initially empty, will be populated by parser)
            spdx_info = SPDXInfo()

            return FileInfo(
                filepath=filepath,
                language=language,
                content=content,
                encoding=encoding,
                line_endings=line_endings,
                has_shebang=has_shebang,
                spdx_info=spdx_info,
                size=size,
                last_modified=last_modified,
                is_binary=is_binary,
                is_empty=is_empty,
            )

        except Exception as e:
            logger.error(f"Error processing file {filepath}: {e}")
            return None

    def _walk_directory(self, directory: Path):
        """Walk directory with optional symlink following."""
        if self.follow_symlinks:
            return directory.walk()
        else:
            return directory.walk(follow_symlinks=False)

    def _is_likely_binary(self, filepath: Path) -> bool:
        """Check if file is likely binary based on extension."""
        binary_extensions = {
            '.exe', '.dll', '.so', '.dylib', '.a', '.o', '.obj',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg',
            '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv',
            '.zip', '.tar', '.gz', '.bz2', '.xz', '.7z', '.rar',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.db', '.sqlite', '.sqlite3',
            '.pyc', '.pyo', '.pyd',
            '.git', '.gitignore', '.gitattributes',
        }

        return filepath.suffix.lower() in binary_extensions

    def get_supported_languages(self) -> Set[str]:
        """Get set of supported programming languages."""
        return set(self.language_detector.LANGUAGE_EXTENSIONS.values())

    def is_language_supported(self, language: str) -> bool:
        """Check if a language is supported."""
        return language in self.get_supported_languages()


def create_default_scanner(
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
) -> FileScanner:
    """Create a file scanner with sensible defaults."""
    # Default include patterns for source code files
    default_include = [
        "**/*.py", "**/*.js", "**/*.ts", "**/*.jsx", "**/*.tsx",
        "**/*.java", "**/*.c", "**/*.cpp", "**/*.h", "**/*.hpp",
        "**/*.go", "**/*.rs", "**/*.rb", "**/*.php", "**/*.swift",
        "**/*.kt", "**/*.scala", "**/*.m", "**/*.mm", "**/*.pl",
        "**/*.lua", "**/*.dart", "**/*.vue", "**/*.svelte",
        "**/*.sh", "**/*.bash", "**/*.zsh", "**/*.fish",
        "**/*.html", "**/*.htm", "**/*.css", "**/*.scss", "**/*.sass", "**/*.less",
        "**/*.json", "**/*.yaml", "**/*.yml", "**/*.toml", "**/*.xml",
    ]

    # Default exclude patterns
    default_exclude = [
        "**/node_modules/**",
        "**/build/**",
        "**/dist/**",
        "**/.git/**",
        "**/__pycache__/**",
        "**/*.egg-info/**",
        "**/venv/**",
        "**/env/**",
        "**/.venv/**",
        "**/.env/**",
        "**/target/**",
        "**/out/**",
        "**/bin/**",
        "**/obj/**",
        "**/.pytest_cache/**",
        "**/.mypy_cache/**",
        "**/coverage/**",
        "**/htmlcov/**",
        "**/.tox/**",
        "**/.nox/**",
    ]

    return FileScanner(
        include_patterns=include_patterns or default_include,
        exclude_patterns=exclude_patterns or default_exclude,
        follow_symlinks=False,
        max_file_size=10 * 1024 * 1024,  # 10MB
    )