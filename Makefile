.PHONY: help install test lint format run docker-build docker-up docker-down clean

help:
	@echo "Learning Resource Curator - Makefile Commands"
	@echo ""
	@echo "Development:"
	@echo "  install       Install dependencies"
	@echo "  test          Run tests"
	@echo "  lint          Run linters"
	@echo "  format        Format code"
	@echo "  run           Run development server"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build  Build Docker images"
	@echo "  docker-up     Start Docker services"
	@echo "  docker-down   Stop Docker services"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean         Remove build artifacts"

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term

lint:
	flake8 src/ tests/
	mypy src/

format:
	black src/ tests/
	isort src/ tests/

run:
	python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f app

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf dist
	rm -rf build

