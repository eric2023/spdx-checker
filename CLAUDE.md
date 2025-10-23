# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is **SPDX Scanner** - an automatic SPDX (Software Package Data Exchange) license declaration scanner and corrector for source code files. The tool scans project source code, identifies missing or incorrect SPDX license declarations, and automatically corrects them according to SPDX specification standards.

## Key Architecture

### Core Components
- **CLI Interface** (`src/spdx_scanner/cli.py`): Command-line interface using Click framework with Rich for enhanced output
- **File Scanner** (`src/spdx_scanner/scanner.py`): Recursively scans directories and identifies files to process
- **SPDX Parser** (`src/spdx_scanner/parser.py`): Extracts and parses existing SPDX license declarations from source files
- **Validator** (`src/spdx_scanner/validator.py`): Validates SPDX declarations against specification standards
- **Corrector** (`src/spdx_scanner/corrector.py`): Automatically fixes missing or incorrect license declarations
- **Reporter** (`src/spdx_scanner/reporter.py`): Generates reports in multiple formats (JSON, HTML, Markdown, CSV)
- **Configuration** (`src/spdx_scanner/config.py`): Manages project configuration and settings
- **Git Integration** (`src/spdx_scanner/git_integration.py`): Provides Git hooks and Git-aware scanning

### Data Models
- **SPDXInfo**: Represents SPDX license information (license identifier, copyright, etc.)
- **FileInfo**: Contains file metadata and SPDX analysis results
- **ValidationResult**: Results from SPDX validation checks
- **CorrectionResult**: Results from automatic correction operations

## Development Commands

### Setup and Installation
```bash
# Install in development mode with all dependencies
make install-dev

# Install pre-commit hooks
pre-commit install
```

### Testing
```bash
# Run all tests
make test

# Run tests with coverage report
make test-coverage

# Run specific test file
pytest tests/test_scanner.py -v

# Run tests with specific markers
pytest tests/ -m "not slow" -v
```

### Code Quality
```bash
# Run all linting checks (flake8, black, isort)
make lint

# Format code with black and isort
make format

# Type checking with mypy
make type-check

# Run all quality checks
make check
```

### Build and Distribution
```bash
# Clean build artifacts
make clean

# Build package distributions
make build

# Upload to PyPI (requires credentials)
make upload
```

### Documentation
```bash
# Build documentation
make docs
```

## Usage Examples

### Command Line Usage
```bash
# Scan directory for SPDX issues
spdx-scanner scan /path/to/project

# Automatically correct SPDX issues
spdx-scanner correct /path/to/project

# Dry run to preview changes
spdx-scanner correct --dry-run /path/to/project

# Generate HTML report
spdx-scanner scan --format html --output report.html /path/to/project

# Install Git pre-commit hook
spdx-scanner install-hook
```

## Configuration

The tool supports configuration via `spdx-scanner.config.json`:
- `default_license`: Default license identifier (e.g., "MIT")
- `project_name`: Project name for copyright notices
- `copyright_holder`: Copyright holder name
- `file_patterns`: Glob patterns for files to scan
- `exclude_patterns`: Glob patterns for files to exclude
- `templates`: Language-specific SPDX header templates

## Testing Strategy

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions
- **Benchmark Tests**: Performance testing using pytest-benchmark
- **Hypothesis Tests**: Property-based testing for robustness

## Important Notes

- The project uses modern Python packaging with `pyproject.toml` as the primary configuration
- Type hints are enforced with strict mypy configuration
- Code formatting follows Black and isort standards
- Test coverage is tracked and should be maintained
- The tool supports multiple programming languages with appropriate comment syntax
- Git integration includes pre-commit hooks for automated SPDX checking