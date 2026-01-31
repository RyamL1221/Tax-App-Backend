.PHONY: help localstack-start localstack-stop localstack-logs localstack-init test test-local deploy-local clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

localstack-start: ## Start LocalStack in Docker
	@echo "Starting LocalStack..."
	docker-compose up -d
	@echo "Waiting for LocalStack to be ready..."
	@sleep 10
	@echo "LocalStack is ready at http://localhost:4566"

localstack-stop: ## Stop LocalStack
	@echo "Stopping LocalStack..."
	docker-compose down

localstack-logs: ## View LocalStack logs
	docker-compose logs -f localstack

localstack-init: ## Initialize LocalStack resources (run after localstack-start)
	@echo "Initializing LocalStack resources..."
	@bash init-localstack.sh

localstack-status: ## Check LocalStack status
	@echo "Checking LocalStack status..."
	@curl -s http://localhost:4566/_localstack/health | python3 -m json.tool || echo "LocalStack is not running"

view-db: ## View DynamoDB table contents
	@echo "Viewing UsersTable contents..."
	@awslocal dynamodb scan --table-name UsersTable --region us-east-1 | python3 -m json.tool

view-db-simple: ## View DynamoDB table contents (simple format)
	@python3 view-dynamodb.py

test: ## Run all tests
	@echo "Running tests..."
	source venv/bin/activate && pytest user_registration/tests/ -v

test-local: localstack-start ## Run tests against LocalStack
	@echo "Running tests against LocalStack..."
	@sleep 5
	@export AWS_ENDPOINT_URL=http://localhost:4566 && \
	export AWS_ACCESS_KEY_ID=test && \
	export AWS_SECRET_ACCESS_KEY=test && \
	export USER_TABLE_NAME=UsersTable && \
	source venv/bin/activate && pytest user_registration/tests/ -v

deploy-local: localstack-start ## Deploy to LocalStack using SAM
	@echo "Deploying to LocalStack..."
	@sleep 5
	samlocal build
	samlocal deploy --guided

sam-start: ## Start SAM local API Gateway with LocalStack connection
	@echo "Starting SAM local API Gateway..."
	@echo "Make sure LocalStack is running first (make localstack-start)"
	sam local start-api --docker-network tax-app-network --parameter-overrides Environment=local

sam-build-local: ## Build SAM for local development
	@echo "Building SAM for local development..."
	sam build --parameter-overrides Environment=local

sam-build-prod: ## Build SAM for production deployment
	@echo "Building SAM for production deployment..."
	sam build --parameter-overrides Environment=production

invoke-local: ## Invoke Lambda function locally against LocalStack
	@echo "Invoking Lambda function..."
	awslocal lambda invoke \
		--function-name UserRegistrationFunction \
		--payload '{"body": "{\"email\":\"test@example.com\",\"name\":\"Test User\",\"password\":\"SecurePass123!\"}"}' \
		response.json
	@cat response.json
	@rm response.json

clean: ## Clean up generated files and stop LocalStack
	@echo "Cleaning up..."
	docker-compose down -v
	rm -rf .aws-sam
	rm -rf localstack-data
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

install: ## Install dependencies
	@echo "Installing dependencies..."
	pip install -r user_registration/requirements.txt
	pip install -r user_registration/tests/requirements-dev.txt
	pip install awscli-local

setup: install localstack-start localstack-init ## Complete setup (install + start LocalStack)
	@echo "Setup complete! LocalStack is running at http://localhost:4566"
