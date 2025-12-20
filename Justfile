# Justfile for Personal Stock Screener
# Alternative to poe for those who prefer just (https://github.com/casey/just)

# List all available commands
default:
    @just --list

# Setup project with uv
setup:
    #!/usr/bin/env bash
    if ! command -v uv &> /dev/null; then
        echo "Installing uv..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
    fi
    uv venv
    source .venv/bin/activate
    uv pip install -e ".[dev]"
    echo "✅ Setup complete! Run 'just docker-up' to start services"

# Format code with black and ruff
format:
    black src tests
    ruff check --fix src tests

# Run linting checks
lint:
    black --check src tests
    ruff check src tests
    mypy src

# Run tests
test:
    pytest tests/ -v

# Run tests with coverage
test-cov:
    pytest tests/ -v --cov=src --cov-report=html --cov-report=term

# Start all Docker services
docker-up:
    docker-compose up -d

# Stop all Docker services
docker-down:
    docker-compose down

# View Docker logs
docker-logs:
    docker-compose logs -f

# Restart all services
docker-restart:
    docker-compose restart

# Initialize database
init-db:
    docker-compose exec backend python init_db.py

# Ingest fundamental data
ingest-fundamentals:
    docker-compose exec backend python -c "from src.tasks.ingestion_tasks import ingest_fundamental_data; print(ingest_fundamental_data())"

# Ingest news data
ingest-news:
    docker-compose exec backend python -c "from src.tasks.ingestion_tasks import ingest_news_data; print(ingest_news_data())"

# Analyze sentiment
analyze-sentiment:
    docker-compose exec backend python -c "from src.tasks.ingestion_tasks import analyze_pending_sentiment; print(analyze_pending_sentiment())"

# Compute scores
compute-scores:
    docker-compose exec backend python -c "from src.tasks.scoring_tasks import compute_all_scores; print(compute_all_scores())"

# Run full data pipeline
run-pipeline: ingest-fundamentals ingest-news analyze-sentiment compute-scores
    echo "✅ Data pipeline complete!"

# Run development server
dev:
    uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Clean up generated files
clean:
    find . -type d -name __pycache__ -exec rm -rf {} +
    find . -type f -name '*.pyc' -delete
    rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov

# Open API documentation in browser
docs:
    open http://localhost:8000/docs

# Open Flower (Celery monitoring)
flower:
    open http://localhost:5555

# Check health of all services
health:
    @echo "Checking API health..."
    @curl -s http://localhost:8000/health | jq .
    @echo "\nChecking Docker services..."
    @docker-compose ps
