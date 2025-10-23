# SPDX Scanner Usage Guide

This guide provides comprehensive instructions for using the SPDX Scanner tool to manage license declarations in your source code files.

## Table of Contents

- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Commands](#commands)
- [Configuration](#configuration)
- [Examples](#examples)
- [Git Integration](#git-integration)
- [Advanced Usage](#advanced-usage)
- [Troubleshooting](#troubleshooting)

## Installation

### From PyPI (when published)
```bash
pip install spdx-scanner
```

### From Source
```bash
git clone https://github.com/example/spdx-scanner.git
cd spdx-scanner
pip install -e .
```

### Development Installation
```bash
git clone https://github.com/example/spdx-scanner.git
cd spdx-scanner
pip install -e ".[dev]"
```

## Basic Usage

### Scan a directory for SPDX issues
```bash
spdx-scanner scan /path/to/project
```

### Automatically correct SPDX issues
```bash
spdx-scanner correct /path/to/project
```

### Preview changes without modifying files
```bash
spdx-scanner correct --dry-run /path/to/project
```

### Generate detailed report
```bash
spdx-scanner scan --format html --output report.html /path/to/project
```

## Commands

### `scan` - Scan for SPDX issues

Scan source code files and identify missing or incorrect SPDX license declarations.

```bash
spdx-scanner scan [OPTIONS] PATH
```

**Options:**
- `--format, -f`: Output format (text, json, html, markdown, csv)
- `--output, -o`: Output file path
- `--include`: Include file patterns (can be used multiple times)
- `--exclude`: Exclude file patterns (can be used multiple times)
- `--follow-symlinks`: Follow symbolic links
- `--max-file-size`: Maximum file size to process (bytes)

**Examples:**
```bash
# Basic scan
spdx-scanner scan ./src

# Generate JSON report
spdx-scanner scan --format json --output results.json ./src

# Scan specific file types
spdx-scanner scan --include "**/*.py" --include "**/*.js" ./src

# Exclude test files
spdx-scanner scan --exclude "**/test_*" --exclude "**/tests/**" ./src
```

### `correct` - Correct SPDX issues

Automatically correct and complete missing SPDX license declarations.

```bash
spdx-scanner correct [OPTIONS] PATH
```

**Options:**
- `--dry-run`: Preview changes without modifying files
- `--backup/--no-backup`: Create backup files before correction (default: --backup)
- `--license`: Default license identifier
- `--copyright-holder`: Default copyright holder
- `--project-name`: Default project name
- `--include`: Include file patterns (can be used multiple times)
- `--exclude`: Exclude file patterns (can be used multiple times)

**Examples:**
```bash
# Correct all files
spdx-scanner correct ./src

# Preview changes
spdx-scanner correct --dry-run ./src

# Correct without backups
spdx-scanner correct --no-backup ./src

# Use specific license
spdx-scanner correct --license "Apache-2.0" --copyright-holder "My Company" ./src
```

### `validate` - Validate SPDX declarations

Validate SPDX license declarations without generating full reports.

```bash
spdx-scanner validate [OPTIONS] PATH
```

**Options:**
- `--format, -f`: Output format (text, json, html, markdown, csv)
- `--output, -o`: Output file path

**Examples:**
```bash
# Validate files
spdx-scanner validate ./src

# Generate validation report
spdx-scanner validate --format json --output validation.json ./src
```

### `init` - Initialize configuration

Create a default configuration file for your project.

```bash
spdx-scanner init [OPTIONS]
```

**Options:**
- `--path`: Project path for configuration (default: current directory)
- `--format`: Configuration file format (json, toml)

**Examples:**
```bash
# Initialize in current directory
spdx-scanner init

# Initialize in specific directory
spdx-scanner init --path ./my-project

# Use TOML format
spdx-scanner init --format toml
```

### `install-hook` - Install Git pre-commit hook

Install a pre-commit hook that validates SPDX declarations before commits.

```bash
spdx-scanner install-hook
```

**Examples:**
```bash
# Install hook in current repository
spdx-scanner install-hook

# The hook will validate SPDX declarations before each commit
```

## Configuration

Create a `spdx-scanner.config.json` file in your project root:

```json
{
  "project_name": "My Project",
  "project_version": "1.0.0",
  "copyright_holder": "My Company",
  "default_license": "MIT",
  "validation_rules": {
    "require_license_identifier": true,
    "require_copyright": true,
    "require_project_attribution": false,
    "allow_unknown_licenses": false,
    "require_osi_approved": false,
    "require_spdx_version": false,
    "min_copyright_year": 1970,
    "max_copyright_year": 2030,
    "copyright_format": "standard",
    "license_format": "strict"
  },
  "correction_settings": {
    "create_backups": true,
    "backup_suffix": ".spdx-backup",
    "preserve_existing": true,
    "default_license": "MIT",
    "default_copyright_holder": "My Company",
    "default_project_name": "My Project",
    "dry_run": false
  },
  "scanner_settings": {
    "follow_symlinks": false,
    "max_file_size": 10485760,
    "include_patterns": [
      "**/*.py",
      "**/*.js",
      "**/*.ts",
      "**/*.java",
      "**/*.c",
      "**/*.cpp"
    ],
    "exclude_patterns": [
      "**/node_modules/**",
      "**/build/**",
      "**/dist/**",
      "**/.git/**",
      "**/__pycache__/**",
      "**/*.egg-info/**",
      "**/venv/**",
      "**/env/**"
    ]
  },
  "output_settings": {
    "format": "text",
    "output_file": null,
    "verbose": false,
    "quiet": false,
    "show_progress": true,
    "include_summary": true,
    "include_details": true
  },
  "git_settings": {
    "enabled": true,
    "respect_gitignore": true,
    "use_git_timestamps": true,
    "check_uncommitted": false,
    "check_untracked": false
  },
  "template_settings": {
    "templates": {
      "python": "# SPDX-License-Identifier: {license}\\n# Copyright (c) {year} {copyright_holder}\\n# {project_name}\\n\\n",
      "javascript": "// SPDX-License-Identifier: {license}\\n// Copyright (c) {year} {copyright_holder}\\n// {project_name}\\n\\n",
      "c": "/* SPDX-License-Identifier: {license}\\n * Copyright (c) {year} {copyright_holder}\\n * {project_name}\\n */\\n\\n"
    },
    "use_custom_templates": false,
    "template_directory": null
  }
}
```

## Examples

### Example 1: Basic Python Project

```bash
# Initialize configuration
spdx-scanner init

# Edit spdx-scanner.config.json to set your project details
# Scan for issues
spdx-scanner scan .

# Correct issues
spdx-scanner correct .

# Install Git hook
spdx-scanner install-hook
```

### Example 2: Multi-language Project

```bash
# Scan Python and JavaScript files
spdx-scanner scan --include "**/*.py" --include "**/*.js" --include "**/*.ts" .

# Correct with custom license
spdx-scanner correct --license "Apache-2.0" --copyright-holder "My Company" .

# Generate HTML report
spdx-scanner scan --format html --output spdx-report.html .
```

### Example 3: CI/CD Integration

```bash
# Validate in CI pipeline
spdx-scanner validate --format json --output validation-results.json .

# Check exit code for CI
if [ $? -ne 0 ]; then
    echo "SPDX validation failed"
    exit 1
fi
```

### Example 4: Dry Run and Review

```bash
# Preview changes
spdx-scanner correct --dry-run --format markdown --output preview.md .

# Review the preview
less preview.md

# Apply changes if satisfied
spdx-scanner correct .
```

## Git Integration

### Install Pre-commit Hook

The pre-commit hook validates SPDX declarations before each commit:

```bash
spdx-scanner install-hook
```

### Hook Behavior

- Validates all staged files before commit
- Prevents commits with invalid SPDX declarations
- Provides helpful error messages
- Can be bypassed with `git commit --no-verify` if needed

### Manual Hook Execution

You can manually run the pre-commit validation:

```bash
# Check what the hook would validate
git diff --cached --name-only | xargs spdx-scanner validate
```

## Advanced Usage

### Custom Templates

Create custom license header templates for different languages:

```json
{
  "template_settings": {
    "templates": {
      "python": "# SPDX-License-Identifier: {license}\\n# Copyright (c) {year} {copyright_holder}\\n# {project_name}\\n#\\n# Additional custom information\\n\\n",
      "javascript": "/**\\n * SPDX-License-Identifier: {license}\\n * Copyright (c) {year} {copyright_holder}\\n * {project_name}\\n */\\n\\n"
    }
  }
}
```

### Complex License Expressions

Support for complex license expressions:

```bash
# Dual licensing
spdx-scanner correct --license "MIT OR Apache-2.0" .

# With exceptions
spdx-scanner correct --license "GPL-3.0 WITH Classpath-exception-2.0" .
```

### Batch Processing

Process multiple directories:

```bash
# Process multiple projects
for project in project1 project2 project3; do
    echo "Processing $project"
    spdx-scanner scan "$project"
    spdx-scanner correct "$project"
done
```

### Integration with Make

Add to your Makefile:

```makefile
.PHONY: spdx-check spdx-fix spdx-report

spdx-check:
	spdx-scanner validate .

spdx-fix:
	spdx-scanner correct .

spdx-report:
	spdx-scanner scan --format html --output spdx-report.html .

# CI target
ci-spdx: spdx-check
	@if [ $$? -ne 0 ]; then \
		echo "SPDX validation failed"; \
		exit 1; \
	fi
```

## Troubleshooting

### Common Issues

**1. Command not found**
```bash
# Make sure spdx-scanner is installed
pip install spdx-scanner

# Or install from source
pip install -e .
```

**2. Permission denied errors**
```bash
# Check file permissions
ls -la problematic_file.py

# Fix permissions
chmod 644 problematic_file.py
```

**3. Git hook not working**
```bash
# Check if hook exists
ls -la .git/hooks/pre-commit

# Make sure hook is executable
chmod +x .git/hooks/pre-commit

# Test hook manually
.git/hooks/pre-commit
```

**4. Large files causing issues**
```bash
# Increase file size limit
spdx-scanner scan --max-file-size 52428800 .  # 50MB

# Or exclude large files
spdx-scanner scan --exclude "**/*.min.js" --exclude "**/vendor/**" .
```

### Debug Mode

Enable verbose output for debugging:

```bash
spdx-scanner --verbose scan .
```

### Getting Help

```bash
# General help
spdx-scanner --help

# Command-specific help
spdx-scanner scan --help
spdx-scanner correct --help
```

### Report Issues

If you encounter issues:

1. Check the troubleshooting section above
2. Enable verbose mode for detailed error messages
3. Report issues at: https://github.com/example/spdx-scanner/issues

Include:
- Command used
- Error message
- Operating system
- Python version
- Configuration file (if applicable)