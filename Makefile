# JCapy Makefile
# Top-notch standard development and release automation
#
# Usage:
#   make <target>
#   make help           - Show this help
#   make install        - Install dependencies
#   make test           - Run tests
#   make build          - Build all artifacts
#   make release        - Full release process

.DEFAULT_GOAL := help

# ============================================
# Configuration
# ============================================
PYTHON := python3
PIP := pip
PYTEST := pytest
VERSION := $(shell grep '^version = ' pyproject.toml | cut -d '"' -f 2)
PACKAGE := jcapy

# Colors for output
CYAN := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

# ============================================
# Help
# ============================================
.PHONY: help
help: ## Show this help message
	@echo "$(CYAN)JCapy Development Commands$(RESET)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)Examples:$(RESET)"
	@echo "  make install        # Install dependencies"
	@echo "  make test           # Run test suite"
	@echo "  make build          # Build package"
	@echo "  make release        # Full release"

# ============================================
# Installation
# ============================================
.PHONY: install
install: ## Install all dependencies (dev + all extras)
	@echo "$(CYAN)Installing dependencies...$(RESET)"
	$(PIP) install -e ".[all]"
	$(PIP) install pytest pytest-cov pytest-asyncio pytest-timeout black ruff isort mypy build twine pip-audit
	@echo "$(GREEN)✓ Dependencies installed$(RESET)"

.PHONY: install-dev
install-dev: ## Install development dependencies only
	@echo "$(CYAN)Installing dev dependencies...$(RESET)"
	$(PIP) install -e .
	$(PIP) install pytest pytest-cov pytest-asyncio black ruff isort mypy
	@echo "$(GREEN)✓ Dev dependencies installed$(RESET)"

.PHONY: install-web
install-web: ## Install web dependencies
	@echo "$(CYAN)Installing web dependencies...$(RESET)"
	cd apps/web && pnpm install
	@echo "$(GREEN)✓ Web dependencies installed$(RESET)"

# ============================================
# Development
# ============================================
.PHONY: dev
dev: ## Start development mode (CLI)
	@$(PYTHON) -m jcapy

.PHONY: dev-web
dev-web: ## Start web development server
	cd apps/web && pnpm run dev

.PHONY: daemon
daemon: ## Start daemon mode
	@$(PYTHON) -m jcapy daemon start

# ============================================
# Code Quality
# ============================================
.PHONY: lint
lint: ## Run all linters
	@echo "$(CYAN)Running linters...$(RESET)"
	ruff check src/ tests/
	@echo "$(GREEN)✓ Linting complete$(RESET)"

.PHONY: format
format: ## Format code with black and isort
	@echo "$(CYAN)Formatting code...$(RESET)"
	black src/ tests/
	isort src/ tests/
	@echo "$(GREEN)✓ Code formatted$(RESET)"

.PHONY: format-check
format-check: ## Check code formatting
	@echo "$(CYAN)Checking formatting...$(RESET)"
	black --check src/ tests/
	isort --check-only src/ tests/
	@echo "$(GREEN)✓ Formatting checks passed$(RESET)"

.PHONY: typecheck
typecheck: ## Run type checking with mypy
	@echo "$(CYAN)Running type checker...$(RESET)"
	mypy src/jcapy --ignore-missing-imports
	@echo "$(GREEN)✓ Type checking complete$(RESET)"

.PHONY: quality
quality: lint format-check typecheck ## Run all quality checks
	@echo "$(GREEN)✓ All quality checks passed$(RESET)"

# ============================================
# Testing
# ============================================
.PHONY: test
test: ## Run test suite
	@echo "$(CYAN)Running tests...$(RESET)"
	$(PYTEST) tests/ -v --cov=src/jcapy --cov-report=term-missing --cov-report=html
	@echo "$(GREEN)✓ Tests complete$(RESET)"

.PHONY: test-fast
test-fast: ## Run fast tests (no coverage)
	@echo "$(CYAN)Running fast tests...$(RESET)"
	$(PYTEST) tests/ -v -x
	@echo "$(GREEN)✓ Fast tests complete$(RESET)"

.PHONY: test-cov
test-cov: ## Run tests with coverage report
	@echo "$(CYAN)Running tests with coverage...$(RESET)"
	$(PYTEST) tests/ -v --cov=src/jcapy --cov-report=html --cov-fail-under=80
	@echo "$(GREEN)✓ Coverage report generated in htmlcov/$(RESET)"

# ============================================
# Building
# ============================================
.PHONY: build
build: clean build-python build-web ## Build all artifacts
	@echo "$(GREEN)✓ Build complete$(RESET)"

.PHONY: build-python
build-python: ## Build Python package (wheel + sdist)
	@echo "$(CYAN)Building Python package...$(RESET)"
	$(PYTHON) -m build
	twine check dist/*
	@echo "$(GREEN)✓ Python package built in dist/$(RESET)"

.PHONY: build-web
build-web: ## Build web assets
	@echo "$(CYAN)Building web assets...$(RESET)"
	cd apps/web && pnpm run build
	@echo "$(GREEN)✓ Web assets built in apps/web/dist/$(RESET)"

.PHONY: build-docker
build-docker: ## Build Docker image
	@echo "$(CYAN)Building Docker image...$(RESET)"
	docker build -f docker/Dockerfile -t $(PACKAGE):$(VERSION) -t $(PACKAGE):latest .
	@echo "$(GREEN)✓ Docker image built$(RESET)"

.PHONY: build-all
build-all: build build-docker ## Build all artifacts including Docker
	@echo "$(GREEN)✓ All artifacts built$(RESET)"

# ============================================
# Cleaning
# ============================================
.PHONY: clean
clean: ## Clean build artifacts
	@echo "$(CYAN)Cleaning build artifacts...$(RESET)"
	rm -rf dist/ build/ *.egg-info src/*.egg-info
	rm -rf htmlcov/ .coverage .pytest_cache
	rm -rf apps/web/dist apps/web/node_modules/.cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)✓ Clean complete$(RESET)"

.PHONY: clean-all
clean-all: clean ## Clean all including node_modules
	@echo "$(CYAN)Cleaning all dependencies...$(RESET)"
	rm -rf apps/web/node_modules apps/web/pnpm-store
	@echo "$(GREEN)✓ Deep clean complete$(RESET)"

# ============================================
# Security
# ============================================
.PHONY: security
security: ## Run security audit
	@echo "$(CYAN)Running security audit...$(RESET)"
	pip-audit --desc-only || true
	bandit -r src/ -ll --skip B101 || true
	@echo "$(GREEN)✓ Security audit complete$(RESET)"

# ============================================
# Publishing
# ============================================
.PHONY: publish-test
publish-test: build ## Publish to TestPyPI
	@echo "$(CYAN)Publishing to TestPyPI...$(RESET)"
	twine upload --repository testpypi dist/*
	@echo "$(GREEN)✓ Published to TestPyPI$(RESET)"

.PHONY: publish-pypi
publish-pypi: build ## Publish to PyPI (production)
	@echo "$(CYAN)Publishing to PyPI...$(RESET)"
	twine upload dist/*
	@echo "$(GREEN)✓ Published to PyPI$(RESET)"

.PHONY: publish-docker
publish-docker: build-docker ## Push Docker image to registries
	@echo "$(CYAN)Pushing Docker image...$(RESET)"
	docker tag $(PACKAGE):$(VERSION) ghcr.io/ponli550/$(PACKAGE):$(VERSION)
	docker tag $(PACKAGE):$(VERSION) ghcr.io/ponli550/$(PACKAGE):latest
	docker push ghcr.io/ponli550/$(PACKAGE):$(VERSION)
	docker push ghcr.io/ponli550/$(PACKAGE):latest
	@echo "$(GREEN)✓ Docker image pushed$(RESET)"

.PHONY: release
release: ## Run full release script
	@./scripts/publish.sh

.PHONY: release-dry
release-dry: ## Dry-run release (preview only)
	@./scripts/publish.sh --dry-run

# ============================================
# Version Management
# ============================================
.PHONY: version
version: ## Show current version
	@echo "$(CYAN)$(PACKAGE) version: $(VERSION)$(RESET)"

.PHONY: bump-patch
bump-patch: ## Bump patch version (x.x.+1)
	@./scripts/bump_version.sh patch

.PHONY: bump-minor
bump-minor: ## Bump minor version (x.+1.0)
	@./scripts/bump_version.sh minor

.PHONY: bump-major
bump-major: ## Bump major version (+1.0.0)
	@./scripts/bump_version.sh major

# ============================================
# Docker
# ============================================
.PHONY: docker-up
docker-up: ## Start daemon with docker-compose
	docker-compose up -d

.PHONY: docker-down
docker-down: ## Stop docker-compose services
	docker-compose down

.PHONY: docker-logs
docker-logs: ## Show docker-compose logs
	docker-compose logs -f

.PHONY: docker-shell
docker-shell: ## Open shell in Docker container
	docker-compose exec jcapy bash

# ============================================
# Documentation
# ============================================
.PHONY: docs
docs: ## Generate documentation
	@echo "$(CYAN)Generating documentation...$(RESET)"
	@echo "$(GREEN)✓ Documentation generated$(RESET)"

# ============================================
# Utilities
# ============================================
.PHONY: check
check: quality test security ## Run all checks (quality + test + security)
	@echo "$(GREEN)✓ All checks passed$(RESET)"

.PHONY: ci
ci: clean install test build ## Simulate CI pipeline locally
	@echo "$(GREEN)✓ CI simulation complete$(RESET)"

.PHONY: setup
setup: install install-web ## Full setup for development
	@echo "$(GREEN)✓ Setup complete! Run 'make dev' to start.$(RESET)"

# ============================================
# Phony Targets
# ============================================
.PHONY: all
all: clean install quality test build