# PiStudio Makefile

.PHONY: install dev test clean docs run-gui run-headless examples

# Installation
install:
	./install.sh

dev:
	poetry install
	poetry run pre-commit install

# Testing
test:
	poetry run pytest tests/ -v

test-coverage:
	poetry run pytest tests/ --cov=pistudio --cov-report=html

# Code quality
lint:
	poetry run black --check .
	poetry run isort --check-only .
	poetry run mypy packages/

format:
	poetry run black .
	poetry run isort .

# Running
run-gui:
	poetry run python -m apps.desktop

run-server:
	poetry run python -m apps.server

run-headless:
	poetry run pistudio run --headless

# Examples
examples:
	@echo "Available examples:"
	@ls -1 examples/

run-blink:
	cd examples/blink_led && poetry run pistudio run

run-bme280:
	cd examples/i2c_bme280_logger && poetry run pistudio run

# Documentation
docs:
	@echo "Building documentation..."
	# Would build Sphinx docs

# Packaging
build:
	poetry build

publish:
	poetry publish

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf build/ dist/ *.egg-info/
	rm -rf .coverage htmlcov/

# Development helpers
check-deps:
	poetry show --outdated

update-deps:
	poetry update

# CI/CD
ci: lint test

# Help
help:
	@echo "PiStudio Development Commands:"
	@echo ""
	@echo "Setup:"
	@echo "  make install     - Install PiStudio"
	@echo "  make dev         - Setup development environment"
	@echo ""
	@echo "Testing:"
	@echo "  make test        - Run tests"
	@echo "  make test-coverage - Run tests with coverage"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint        - Check code style"
	@echo "  make format      - Format code"
	@echo ""
	@echo "Running:"
	@echo "  make run-gui     - Launch desktop GUI"
	@echo "  make run-server  - Launch headless server"
	@echo "  make run-blink   - Run LED blink example"
	@echo "  make run-bme280  - Run BME280 example"
	@echo ""
	@echo "Packaging:"
	@echo "  make build       - Build distribution packages"
	@echo "  make clean       - Clean build artifacts"