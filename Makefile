.PHONY: help localstack-start localstack-stop localstack-logs localstack-init test test-local deploy-local clean check-path fix-path validate-docker-mount

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
	@bash scripts/init-localstack.sh

localstack-status: ## Check LocalStack status
	@echo "Checking LocalStack status..."
	@curl -s http://localhost:4566/_localstack/health | python3 -m json.tool || echo "LocalStack is not running"

view-db: ## View DynamoDB table contents
	@echo "Viewing Users contents..."
	@awslocal dynamodb scan --table-name Users --region us-east-1 | python3 -m json.tool

view-db-simple: ## View DynamoDB table contents (simple format)
	@python3 scripts/utils/view-dynamodb.py

test: ## Run all tests
	@echo "Running tests..."
	source venv/bin/activate && pytest user_registration/tests/ -v

test-local: localstack-start ## Run tests against LocalStack
	@echo "Running tests against LocalStack..."
	@sleep 5
	@export AWS_ENDPOINT_URL=http://localhost:4566 && \
	export AWS_ACCESS_KEY_ID=test && \
	export AWS_SECRET_ACCESS_KEY=test && \
	export USER_TABLE_NAME=Users && \
	source venv/bin/activate && pytest user_registration/tests/ -v

deploy-local: localstack-start ## Deploy to LocalStack using SAM
	@echo "Deploying to LocalStack..."
	@sleep 5
	samlocal build
	samlocal deploy --guided

sam-start: ## Start SAM local API Gateway with LocalStack connection
	@echo "Starting SAM local API Gateway..."
	@echo "Make sure LocalStack is running first (make localstack-start)"
	sam local start-api --docker-network tax-app-network --env-vars env.json

sam-build-local: ## Build SAM for local development
	@echo "Building SAM for local development..."
	sam build

sam-build-prod: ## Build SAM for production deployment
	@echo "Building SAM for production deployment..."
	sam build --parameter-overrides Environment=production

# Docker Path Fix
check-path: ## Check if current project path is Docker-compatible
	@bash scripts/check_docker_path.sh

fix-path: ## Create symlink to a space-free path for Docker compatibility
	@bash scripts/fix_docker_path.sh

validate-docker-mount: ## Test Docker bind mount with build artifacts
	@bash scripts/validate_docker_mount.sh

invoke-local: ## Invoke Lambda function locally against LocalStack
	@echo "Invoking Lambda function..."
	awslocal lambda invoke \
		--function-name UserRegistrationFunction \
		--payload '{"body": "{\"email\":\"test@example.com\",\"name\":\"Test User\",\"password\":\"SecurePass123!\"}"}' \
		response.json
	@cat response.json
	@rm response.json

clean-lambda: ## Stop and remove orphaned Lambda containers from SAM Local
	@echo "Cleaning up Lambda containers..."
	@docker stop $$(docker ps -q --filter "ancestor=public.ecr.aws/lambda/python:3.14-rapid-x86_64") 2>/dev/null || true
	@docker rm $$(docker ps -aq --filter "ancestor=public.ecr.aws/lambda/python:3.14-rapid-x86_64") 2>/dev/null || true
	@echo "Lambda containers cleaned up"

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

test-tax-docs: ## Run tax document generation tests
	@echo "Running tax document generation tests..."
	source venv/bin/activate && pytest tax_document_generation/tests/ -v

test-tax-docs-property: ## Run tax document generation property tests
	@echo "Running tax document generation property tests..."
	source venv/bin/activate && pytest tax_document_generation/tests/ -v -k "property"

test-tax-docs-integration: ## Run tax document generation integration tests (requires LocalStack)
	@echo "Running tax document generation integration tests..."
	@export AWS_ENDPOINT_URL=http://localhost:4566 && \
	export AWS_ACCESS_KEY_ID=test && \
	export AWS_SECRET_ACCESS_KEY=test && \
	source venv/bin/activate && pytest tax_document_generation/tests/test_lambda_handler_integration.py -v

test-tax-docs-endpoint: ## Test tax document generation endpoint with curl
	@echo "Testing tax document generation endpoint..."
	@bash scripts/test-tax-document-generation.sh

deploy-tax-docs: ## Deploy tax document generation function to LocalStack
	@echo "Deploying tax document generation function..."
	samlocal build
	samlocal deploy --no-confirm-changeset

