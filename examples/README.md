# SPDX Scanner Examples

This directory contains examples demonstrating how to use the SPDX Scanner tool.

## Files

- `spdx-scanner.config.json` - Example configuration file
- `example.py` - Python file with proper SPDX license header
- `example.js` - JavaScript file with proper SPDX license header
- `example.c` - C file with proper SPDX license header
- `Makefile` - Example Makefile with SPDX Scanner integration

## Usage Examples

### 1. Basic Scanning

```bash
# Scan current directory
spdx-scanner scan .

# Scan with custom configuration
spdx-scanner --config spdx-scanner.config.json scan .
```

### 2. Automatic Correction

```bash
# Preview changes (dry run)
spdx-scanner correct --dry-run .

# Apply corrections
spdx-scanner correct .

# Correct with specific license
spdx-scanner correct --license "Apache-2.0" --copyright-holder "My Company" .
```

### 3. Report Generation

```bash
# Generate HTML report
spdx-scanner scan --format html --output report.html .

# Generate JSON report for CI integration
spdx-scanner scan --format json --output report.json .

# Generate Markdown report
spdx-scanner scan --format markdown --output report.md .
```

### 4. Makefile Integration

Use the provided Makefile as a template for integrating SPDX Scanner into your build process:

```bash
# Check SPDX compliance
make check-spdx

# Fix SPDX issues
make fix-spdx

# Generate SPDX report
make spdx-report

# Run full CI pipeline
make ci
```

### 5. Configuration Examples

The `spdx-scanner.config.json` file demonstrates various configuration options:

- **Project settings**: Name, version, copyright holder
- **Validation rules**: Requirements for license identifiers, copyright, etc.
- **Correction settings**: Backup creation, default values
- **Scanner settings**: File patterns, exclusions, size limits
- **Output settings**: Report formats, verbosity
- **Git integration**: .gitignore respect, timestamp usage
- **Custom templates**: Language-specific license header formats

### 6. Git Integration

```bash
# Install pre-commit hook
spdx-scanner install-hook

# The hook will validate SPDX declarations before each commit
# To bypass the hook (not recommended): git commit --no-verify
```

## License Header Examples

### Python
```python
# SPDX-License-Identifier: MIT
# Copyright (c) 2023 Example Corporation
# Example Project

# Your code here
```

### JavaScript
```javascript
// SPDX-License-Identifier: MIT
// Copyright (c) 2023 Example Corporation
// Example Project

// Your code here
```

### C/C++
```c
/* SPDX-License-Identifier: MIT
 * Copyright (c) 2023 Example Corporation
 * Example Project
 */

// Your code here
```

### HTML
```html
<!-- SPDX-License-Identifier: MIT -->
<!-- Copyright (c) 2023 Example Corporation -->
<!-- Example Project -->

<!-- Your HTML here -->
```

## Complex License Expressions

The tool supports complex SPDX license expressions:

```bash
# Dual licensing
spdx-scanner correct --license "MIT OR Apache-2.0" .

# With exceptions
spdx-scanner correct --license "GPL-3.0 WITH Classpath-exception-2.0" .

# Multiple licenses
spdx-scanner correct --license "MIT AND BSD-3-Clause" .
```

## CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: SPDX Compliance

on: [push, pull_request]

jobs:
  spdx-check:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.8'

    - name: Install SPDX Scanner
      run: |
        pip install spdx-scanner

    - name: Validate SPDX Declarations
      run: |
        spdx-scanner validate --format json --output spdx-report.json .

    - name: Upload SPDX Report
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: spdx-report
        path: spdx-report.json
```

## Getting Started

1. **Install SPDX Scanner**:
   ```bash
   pip install spdx-scanner
   ```

2. **Initialize configuration**:
   ```bash
   spdx-scanner init
   ```

3. **Edit configuration** to match your project:
   ```bash
   # Edit spdx-scanner.config.json
   # Set your project name, copyright holder, and preferred license
   ```

4. **Scan your project**:
   ```bash
   spdx-scanner scan .
   ```

5. **Fix any issues**:
   ```bash
   spdx-scanner correct .
   ```

6. **Install Git hook** (optional but recommended):
   ```bash
   spdx-scanner install-hook
   ```

## Next Steps

- Review the [usage documentation](../docs/usage.md) for detailed command reference
- Customize the configuration file for your specific needs
- Integrate SPDX scanning into your development workflow
- Set up CI/CD integration for automated compliance checking