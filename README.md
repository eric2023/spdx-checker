# SPDX Scanner

Automatic SPDX (Software Package Data Exchange) license declaration scanner and corrector for source code files.

## Overview

This tool automatically scans project source code files, identifies missing or incorrect SPDX license declarations, and provides functionality to automatically correct and complete them according to UnionTech's open source code declaration requirements and SPDX specification standards.

## Features

- 🔍 **Automatic Detection**: Scans source code files and identifies SPDX license declarations
- 🔧 **Intelligent Correction**: Fixes missing or incorrect license headers automatically
- 🌐 **Multi-Language Support**: Handles various programming languages and comment styles
- ⚙️ **Configuration Management**: Flexible configuration for different project needs
- 📊 **Comprehensive Reporting**: Multiple output formats with detailed statistics
- 🔗 **Git Integration**: Pre-commit hooks and Git-aware scanning
- 🖥️ **CLI Interface**: Professional command-line tool with progress indicators

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

## Quick Start

### Scan a directory for SPDX issues
```bash
spdx-scanner scan /path/to/project
```

### Automatically correct SPDX issues
```bash
spdx-scanner correct /path/to/project
```

### Dry run to preview changes
```bash
spdx-scanner correct --dry-run /path/to/project
```

### Generate detailed report
```bash
spdx-scanner scan --format html --output report.html /path/to/project
```

## Configuration

Create a `spdx-scanner.config.json` file in your project root:

```json
{
  "default_license": "MIT",
  "project_name": "My Project",
  "copyright_holder": "My Company",
  "file_patterns": [
    "**/*.py",
    "**/*.js",
    "**/*.ts"
  ],
  "exclude_patterns": [
    "**/node_modules/**",
    "**/build/**",
    "**/dist/**"
  ],
  "templates": {
    "python": "# SPDX-License-Identifier: {license}\\n# Copyright (c) {year} {copyright_holder}\\n# {project_name}\\n",
    "javascript": "// SPDX-License-Identifier: {license}\\n// Copyright (c) {year} {copyright_holder}\\n// {project_name}\\n"
  }
}
```

## Supported Languages

- Python (.py)
- JavaScript (.js, .jsx)
- TypeScript (.ts, .tsx)
- Java (.java)
- C/C++ (.c, .cpp, .h, .hpp)
- Go (.go)
- Rust (.rs)
- Shell scripts (.sh, .bash)
- HTML (.html, .htm)
- CSS (.css)
- SCSS (.scss)
- And more...

## Git Integration

### Install pre-commit hook
```bash
spdx-scanner install-hook
```

### Manual pre-commit check
```bash
spdx-scanner pre-commit
```

## Output Formats

- **JSON**: Machine-readable format for integration
- **HTML**: Rich report with syntax highlighting
- **Markdown**: GitHub-friendly format
- **Plain Text**: Simple console output
- **CSV**: Spreadsheet-compatible format

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and development process.

## Support

- 📖 [Documentation](https://github.com/example/spdx-scanner/wiki)
- 🐛 [Issue Tracker](https://github.com/example/spdx-scanner/issues)
- 💬 [Discussions](https://github.com/example/spdx-scanner/discussions)

## Acknowledgments

- SPDX specification contributors
- UnionTech for open source code declaration requirements
- Python community for excellent tools and libraries