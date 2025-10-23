# SPDX-License-Identifier: MIT
# Copyright (c) 2023 Example Corporation
# Example Project

# Example Makefile showing SPDX Scanner integration

.PHONY: help install test lint format check-spdx fix-spdx spdx-report clean

# Default target
help:
	@echo "Available targets:"
	@echo "  install      - Install dependencies"
	@echo "  test         - Run tests"
	@echo "  lint         - Run linting"
	@echo "  format       - Format code"
	@echo "  check-spdx   - Check SPDX license declarations"
	@echo "  fix-spdx     - Fix SPDX license declarations"
	@echo "  spdx-report  - Generate SPDX report"
	@echo "  clean        - Clean build artifacts"

# Install dependencies
install:
	pip install -r requirements.txt
	pip install -e .

# Run tests
test:
	pytest tests/ -v

# Run linting
lint:
	flake8 src/ tests/
	mypy src/

# Format code
format:
	black src/ tests/
	isort src/ tests/

# Check SPDX license declarations
check-spdx:
	@echo "Checking SPDX license declarations..."
	spdx-scanner validate --format text .
	@if [ $$? -ne 0 ]; then \
		echo "SPDX validation failed!"; \
		echo "Run 'make fix-spdx' to automatically fix issues."; \
		exit 1; \
	fi
	@echo "SPDX validation passed!"

# Fix SPDX license declarations
fix-spdx:
	@echo "Fixing SPDX license declarations..."
	spdx-scanner correct --format text .
	@echo "SPDX corrections completed!"

# Generate SPDX report
spdx-report:
	@echo "Generating SPDX report..."
	spdx-scanner scan --format html --output spdx-report.html .
	@echo "SPDX report generated: spdx-report.html"

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -f spdx-report.html

# CI target - runs all checks
ci: lint test check-spdx
	@echo "All CI checks passed!"

# Development setup
dev-setup: install
	pre-commit install
	@echo "Development environment setup complete!"

# Pre-commit hook integration
pre-commit: check-spdx
	@echo "Pre-commit checks passed!"