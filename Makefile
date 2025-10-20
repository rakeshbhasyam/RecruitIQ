# RecruitIQ Docker Management Makefile

.PHONY: help build up down logs shell clean test lint format

# Default target
help: ## Show this help message
	@echo "RecruitIQ Docker Management"
	@echo "========================="
	@echo ""
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Development commands
build: ## Build the Docker images
	docker-compose build

up: ## Start the development environment
	docker-compose up -d

down: ## Stop and remove containers
	docker-compose down

logs: ## Show logs from all services
	docker-compose logs -f

logs-api: ## Show logs from API service only
	docker-compose logs -f recruitiq-api

logs-db: ## Show logs from MongoDB service only
	docker-compose logs -f mongodb

# Production commands
prod-build: ## Build production images
	docker-compose -f docker-compose.prod.yml build

prod-up: ## Start production environment
	docker-compose -f docker-compose.prod.yml up -d

prod-down: ## Stop production environment
	docker-compose -f docker-compose.prod.yml down

prod-logs: ## Show production logs
	docker-compose -f docker-compose.prod.yml logs -f

# Development tools
shell: ## Open shell in API container
	docker-compose exec recruitiq-api /bin/bash

shell-db: ## Connect to external MongoDB shell
	@echo "Connect to your external MongoDB using:"
	@echo "mongosh '${MONGODB_URL}'"

# Database commands (for external MongoDB)
db-backup: ## Backup external MongoDB database (requires mongodump on host)
	@echo "Backup your external MongoDB using:"
	@echo "mongodump --uri='${MONGODB_URL}' --out ./backup"

db-restore: ## Restore external MongoDB database (requires mongorestore on host)
	@echo "Restore your external MongoDB using:"
	@echo "mongorestore --uri='${MONGODB_URL}' ./backup"

# Utility commands
clean: ## Clean up Docker resources
	docker-compose down -v
	docker system prune -f
	docker volume prune -f

clean-all: ## Clean up all Docker resources (including images)
	docker-compose down -v --rmi all
	docker system prune -af
	docker volume prune -f

# Health checks
health: ## Check service health
	@echo "Checking API health..."
	@curl -f http://localhost:5000/health || echo "API is not healthy"
	@echo "Checking external MongoDB connection..."
	@echo "Make sure your MongoDB is running and accessible at: ${MONGODB_URL}"

# Development setup
setup: ## Initial setup for development
	@echo "Setting up development environment..."
	@if [ ! -f .env ]; then cp env.example .env; echo "Created .env file from template"; fi
	@echo "Please update .env file with your configuration"
	@echo "Run 'make up' to start the services"

# Testing
test: ## Run tests (if available)
	docker-compose exec recruitiq-api python -m pytest

lint: ## Run linting
	docker-compose exec recruitiq-api python -m flake8 .

format: ## Format code
	docker-compose exec recruitiq-api python -m black .

# Monitoring
stats: ## Show container resource usage
	docker stats

# Quick commands
restart: ## Restart all services
	docker-compose restart

restart-api: ## Restart API service only
	docker-compose restart recruitiq-api

# Full stack with tools
up-tools: ## Start with MongoDB Express
	docker-compose --profile tools up -d

up-nginx: ## Start with Nginx reverse proxy
	docker-compose -f docker-compose.prod.yml --profile nginx up -d
