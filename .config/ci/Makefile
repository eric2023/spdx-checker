# SPDX Scanner Makefile

.PHONY: help install install-dev test test-coverage lint format type-check clean build upload docs

# Default target
help:
	@echo "Available targets:"
	@echo "  install      - Install package in development mode"
	@echo "  install-dev  - Install package with development dependencies"
	@echo "  test         - Run tests"
	@echo "  test-coverage - Run tests with coverage report"
	@echo "  lint         - Run linting checks"
	@echo "  format       - Format code with black and isort"
	@echo "  type-check   - Run mypy type checking"
	@echo "  clean        - Clean build artifacts"
	@echo "  build        - Build package distributions"
	@echo "  upload       - Upload to PyPI (requires credentials)"
	@echo "  docs         - Build documentation"

# Installation targets
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

# Testing targets
test:
	pytest tests/ -v

test-coverage:
	pytest tests/ --cov=src/spdx_scanner --cov-report=html --cov-report=term

# Code quality targets
lint:
	flake8 src/ tests/
	black --check src/ tests/
	isort --check-only src/ tests/

format:
	black src/ tests/
	isort src/ tests/

type-check:
	mypy src/

# Build and distribution targets
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	python -m build

upload: build
	python -m twine upload dist/*

# Documentation targets
docs:
	cd docs && make html

# Development workflow
dev-setup: install-dev
	pre-commit install

check: lint type-check test

# CI/CD targets
ci-test: test-coverage
	codecov

ci-check: lint type-check