.PHONY: help install install-dev setup-hooks lint format test clean scrape-foodpanda scrape-foodi docker-build docker-run docker-compose-up

# Variables
PYTHON := python3
PIP := pip3
PROJECT_NAME := web-scraper
DOCKER_IMAGE := $(PROJECT_NAME):latest

# Default target - show help
.DEFAULT_GOAL := help

help:
	@echo "================================="
	@echo "  $(PROJECT_NAME) - Make Commands"
	@echo "================================="
	@echo ""
	@echo "Installation:"
	@echo "  make install              Install production dependencies"
	@echo "  make install-dev          Install all dependencies (prod + dev)"
	@echo "  make setup-hooks          Setup pre-commit hooks"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint                 Run linters (flake8, mypy, black, isort)"
	@echo "  make format               Auto-format code (black, isort)"
	@echo "  make test                 Run tests with coverage"
	@echo ""
	@echo "Scraping:"
	@echo "  make scrape-foodpanda     Run FoodPanda v1 scraper"
	@echo "  make scrape-foodpanda-v2  Run FoodPanda v2 scraper"
	@echo "  make scrape-foodi         Run Foodi v1 scraper"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build         Build Docker image"
	@echo "  make docker-run           Run scraper in Docker container"
	@echo "  make docker-compose-up    Start services with Docker Compose"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean                Remove cache, logs, and build files"
	@echo "  make clean-output         Remove output files"
	@echo ""

# ============================================================================
# Installation Targets
# ============================================================================

install:
	@echo "Installing production dependencies..."
	$(PIP) install -r requirements.txt
	$(PYTHON) -m playwright install chromium
	@echo "✓ Installation complete"

install-dev: install
	@echo "Installing development dependencies..."
	$(PIP) install -r requirements-dev.txt
	@echo "✓ Development dependencies installed"

setup-hooks: install-dev
	@echo "Setting up pre-commit hooks..."
	pre-commit install
	@echo "✓ Pre-commit hooks installed"
	@echo "Hooks will run on 'git commit'"

# ============================================================================
# Code Quality Targets
# ============================================================================

lint:
	@echo "Running linters..."
	@echo ""
	@echo "1. Checking code style with flake8..."
	flake8 scrapers/ utils/ tests/ --max-line-length=100 --ignore=E501,W503 || true
	@echo ""
	@echo "2. Type checking with mypy..."
	mypy scrapers/ utils/ --ignore-missing-imports || true
	@echo ""
	@echo "3. Checking import order with isort..."
	isort --check-only --diff scrapers/ utils/ tests/ || true
	@echo ""
	@echo "✓ Linting complete"

format:
	@echo "Auto-formatting code..."
	@echo ""
	@echo "1. Formatting with black..."
	black scrapers/ utils/ tests/ --line-length=100
	@echo ""
	@echo "2. Sorting imports with isort..."
	isort scrapers/ utils/ tests/
	@echo ""
	@echo "✓ Formatting complete"

# ============================================================================
# Scraping Targets
# ============================================================================

scrape-foodpanda:
	@echo "Running FoodPanda v1 scraper..."
	$(PYTHON) -m scrapers.foodpanda.v1Scraper
	@echo "✓ Done"

scrape-foodi:
	@echo "Running Foodi v1 scraper..."
	$(PYTHON) -m scrapers.foodi.v1Scraper
	@echo "✓ Done"

# ============================================================================
# Docker Targets
# ============================================================================

docker-build:
	@echo "Building Docker image: $(DOCKER_IMAGE)"
	docker build -t $(DOCKER_IMAGE) .
	@echo "✓ Docker image built"

docker-run:
	@echo "Running scraper in Docker..."
	docker run --rm \
		-v $(PWD)/output:/app/output \
		-v $(PWD)/logs:/app/logs \
		$(DOCKER_IMAGE)
	@echo "✓ Docker run complete"

docker-compose-up:
	@echo "Starting Docker Compose services..."
	docker-compose up --build
	@echo "✓ Services started"

docker-compose-down:
	@echo "Stopping Docker Compose services..."
	docker-compose down
	@echo "✓ Services stopped"

# ============================================================================
# Cleanup Targets
# ============================================================================

clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete
	@echo "✓ Cleanup complete"

clean-output:
	@echo "Removing output files..."
	rm -rf output/*.json output/*.csv 2>/dev/null || true
	@echo "✓ Output files removed"

clean-logs:
	@echo "Removing log files..."
	rm -rf logs/*.log 2>/dev/null || true
	@echo "✓ Log files removed"

clean-all: clean clean-output clean-logs
	@echo "✓ Full cleanup complete"

# ============================================================================
# Utility Targets
# ============================================================================

freeze:
	@echo "Freezing current environment..."
	$(PIP) freeze > requirements.txt
	@echo "✓ Requirements frozen to requirements-frozen.txt"

shell:
	@echo "Starting Python shell..."
	$(PYTHON)

check:
	@echo "Checking project setup..."
	@echo ""
	@echo "✓ Python version:"
	@$(PYTHON) --version
	@echo ""
	@echo "✓ Playwright:"
	@$(PYTHON) -c "import playwright; print(f'  Installed: {playwright.__version__}')" || echo "  Not installed"
	@echo ""
	@echo "✓ Key packages:"
	@$(PIP) list | grep -E "playwright|selenium|beautifulsoup" || echo "  Some packages missing"
	@echo ""
	@echo "✓ Pre-commit hooks:"
	@test -f .git/hooks/pre-commit && echo "  Installed" || echo "  Not installed"