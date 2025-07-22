# Makefile for Caching Platform

.PHONY: help install dev-install test lint format clean build docker-build docker-run k8s-deploy

# Default target
help:
	@echo "Available targets:"
	@echo "  install      - Install production dependencies"
	@echo "  dev-install  - Install development dependencies"
	@echo "  test         - Run all tests"
	@echo "  load-test    - Run load tests"
	@echo "  lint         - Run code linting"
	@echo "  format       - Format code"
	@echo "  clean        - Clean build artifacts"
	@echo "  build        - Build distribution packages"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run   - Run with Docker Compose"
	@echo "  k8s-deploy   - Deploy to Kubernetes"
	@echo "  docs         - Generate documentation"

# Installation targets
install:
	pip install -r requirements.txt
	pip install -e .

dev-install:
	pip install -r requirements.txt
	pip install -e ".[dev]"
	pre-commit install

# Testing targets
test:
	pytest tests/ -v --cov=caching_platform --cov-report=html --cov-report=term

load-test:
	python -m caching_platform test --load-test --duration 300

integration-test:
	pytest tests/integration/ -v

unit-test:
	pytest tests/unit/ -v

# Code quality targets
lint:
	flake8 caching_platform/
	mypy caching_platform/

format:
	black caching_platform/ tests/
	isort caching_platform/ tests/

check: lint test

# Build targets
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	python setup.py sdist bdist_wheel

# Docker targets
docker-build:
	docker build -t caching-platform:latest .

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down

docker-logs:
	docker-compose logs -f caching-platform

# Kubernetes targets
k8s-deploy:
	kubectl apply -f k8s/

k8s-delete:
	kubectl delete -f k8s/

k8s-status:
	kubectl get pods -n caching-platform

k8s-logs:
	kubectl logs -f deployment/caching-platform -n caching-platform

# Development targets
dev-run:
	python -m caching_platform interactive

dev-daemon:
	python -m caching_platform daemon --debug

dev-reset:
	docker-compose down -v
	docker-compose up -d redis
	sleep 5
	python -m caching_platform init-cluster

# Documentation targets
docs:
	sphinx-build -b html docs/ docs/_build/html

docs-serve:
	cd docs/_build/html && python -m http.server 8000

# Monitoring targets
metrics:
	python -m caching_platform metrics --format json

health:
	python -m caching_platform status --verbose

# Backup and restore
backup:
	python -m caching_platform backup --backup-dir ./backups

restore:
	python -m caching_platform restore --backup-file ./backups/latest.tar.gz

# Performance benchmarks
benchmark:
	python -m caching_platform benchmark --duration 60 --clients 10

stress-test:
	python -m caching_platform test --load-test --duration 600 --clients 100

# Security scans
security-scan:
	bandit -r caching_platform/
	safety check

# Release targets
release-patch:
	bumpversion patch
	git push && git push --tags

release-minor:
	bumpversion minor
	git push && git push --tags

release-major:
	bumpversion major
	git push && git push --tags

# Environment setup
setup-dev:
	python -m venv venv
	source venv/bin/activate && make dev-install
	docker-compose up -d redis prometheus grafana

setup-prod:
	make install
	make k8s-deploy

# Monitoring setup
setup-monitoring:
	docker-compose up -d prometheus grafana
	@echo "Grafana available at http://localhost:3000 (admin/admin)"
	@echo "Prometheus available at http://localhost:9091"