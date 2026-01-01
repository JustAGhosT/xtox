.PHONY: install dev-install test test-cov lint format clean build setup run-example md-to-pdf

# Install package in development mode
install:
	pip install -e .

# Install with development dependencies
dev-install:
	pip install -e ".[dev]"

# Run tests
test:
	pytest

# Run tests with coverage
test-cov:
	pytest --cov=xtox --cov-report=html --cov-report=term

# Lint code
lint:
	flake8 xtox
	mypy xtox

# Format code
format:
	black xtox
	isort xtox

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

# Build package
build: clean
	python -m build

# Install all dependencies
setup: dev-install
	pip install -e ".[azure,api]"

# Run the Markdown to PDF example
run-example:
	python examples/md_to_pdf_example.py test_data/test_doc.md output

# Convert a Markdown file to PDF using the CLI
md-to-pdf:
	python -m xtox.cli.main test_data/test_doc.md -o output -r 2

# Run a quick demo of the main pipeline
demo: install
	mkdir -p output
	python -m xtox.cli.main test_data/test_doc.md -o output -r 2 -v