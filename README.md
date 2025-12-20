# Personal Stock Screener - Modern Python Tooling

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2-blue)](https://docs.pydantic.dev/latest/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A production-ready stock screening system for Indian equities combining fundamental analysis and sentiment analysis powered by machine learning.

## 🎯 Features

- **Fundamental Analysis**: Track key financial metrics (PE, PB, ROE, debt ratios, growth metrics)
- **Sentiment Analysis**: ML-powered sentiment analysis of news articles using FinBERT
- **Composite Scoring**: Configurable weighted scoring combining fundamentals and sentiment
- **REST API**: Versioned APIs for stock data, screening, and alerts
- **Real-time Updates**: Scheduled data ingestion with Celery
- **Explainability**: Detailed score breakdowns showing how rankings are computed
- **Production-Ready**: Docker-based deployment, structured logging, health checks

## 🚀 Quick Start

### Prerequisites

- [uv](https://github.com/astral-sh/uv) - Fast Python package installer
- [Docker & Docker Compose](https://www.docker.com/) - For containerized deployment
- Python 3.11+ (if running locally)

### Install uv (if not already installed)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with pip
pip install uv
```

### 1. Clone and Setup

```bash
cd /Users/devaraj/Documents/personal/personal-stock-screener

# Create virtual environment and install dependencies using uv
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"

# Or just install production dependencies
uv pip install -e .

# Copy environment template
cp .env.example .env

# Edit .env and configure as needed
nano .env
```

### 2. Install poethepoet (poe) for task running

```bash
uv pip install poethepoet
```

### 3. Start Services with Docker

```bash
# Using poe task runner
poe docker-up

# Or directly with docker-compose
docker-compose up -d

# Check service health
docker-compose ps
```

### 4. Initialize Database

```bash
# Using poe
poe init-db

# Or directly
docker-compose exec backend python init_db.py
```

### 5. Run Initial Data Pipeline

```bash
# Run all tasks in sequence
poe run-all-tasks

# Or run individual tasks:
poe ingest-fundamentals  # Fetch stock fundamentals
poe ingest-news          # Fetch news articles
poe analyze-sentiment    # Analyze sentiment
poe compute-scores       # Compute composite scores
```

### 6. Access Services

- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/health
- **Celery Monitoring (Flower)**: http://localhost:5555

## 🛠️ Development with Poe

The project uses [poethepoet](https://poethepoet.natn.io/) for task automation. All tasks are defined in `pyproject.toml`.

### Code Quality Tasks

```bash
# Format code with black and ruff
poe format

# Run linting checks
poe lint

# Run tests
poe test

# Run tests with coverage
poe test-cov
```

### Docker Management

```bash
# Start all services
poe docker-up

# Stop all services
poe docker-down

# View logs
poe docker-logs
```

### Data Pipeline Tasks

```bash
# Initialize database
poe init-db

# Ingest fundamentals
poe ingest-fundamentals

# Ingest news
poe ingest-news

# Analyze sentiment
poe analyze-sentiment

# Compute scores
poe compute-scores

# Run all tasks
poe run-all-tasks
```

### Development Server

```bash
# Run development server with auto-reload
poe dev

# Open IPython shell
poe shell

# Clean up generated files
poe clean
```

## 📦 Modern Python Stack

This project uses cutting-edge Python tooling for optimal developer experience:

| Tool | Purpose | Why? |
|------|---------|------|
| **uv** | Package installer | 10-100x faster than pip, Rust-based |
| **pyproject.toml** | Project config | Modern Python standard, one config file |
| **Pydantic v2** | Data validation | 5-50x faster than v1, better type safety |
| **poe (poethepoet)** | Task runner | Simple, powerful, no Makefile needed |
| **Ruff** | Linter & formatter | 10-100x faster than flake8+isort+black |
| **FastAPI** | Web framework | Modern async framework with auto-docs |

### Benefits of this Stack

✅ **10-100x faster dependency installation** with uv  
✅ **Cleaner project structure** with pyproject.toml  
✅ **Better type safety** with Pydantic v2  
✅ **Simpler task automation** with poe  
✅ **Faster linting** with Ruff  

## 🏗️ Project Structure

```
personal-stock-screener/
├── backend/
│   ├── src/
│   │   ├── api/v1/         # REST API endpoints
│   │   ├── core/           # Config, logging, database
│   │   ├── ingestion/      # Data ingestors
│   │   ├── models/         # SQLAlchemy models & Pydantic schemas
│   │   ├── scoring/        # Scoring engines
│   │   ├── sentiment/      # Sentiment analysis (FinBERT)
│   │   └── tasks/          # Celery tasks
│   ├── init_db.py          # Database initialization
│   └── Dockerfile          # Backend container (uv-based)
├── pyproject.toml          # Project config & dependencies
├── docker-compose.yml      # Multi-container setup
├── .env.example            # Environment template
└── README.md
```

## � API Examples

### Get Top Rankings

```bash
# Top 10 by composite score
curl http://localhost:8000/api/v1/screen/rankings/composite?limit=10

# Top 10 by sentiment
curl http://localhost:8000/api/v1/screen/rankings/sentiment?limit=10
```

### Screen Stocks with Filters

```bash
curl -X POST http://localhost:8000/api/v1/screen \
  -H "Content-Type: application/json" \
  -d '{
    "pe_ratio_max": 30,
    "roe_min": 15,
    "debt_to_equity_max": 1.0,
    "composite_score_min": 60,
    "limit": 10,
    "sort_by": "composite_score",
    "sort_order": "desc"
  }'
```

### Get Stock Details

```bash
curl http://localhost:8000/api/v1/stocks/RELIANCE
```

## 🔧 Configuration

All configuration is in `.env` file. Key settings:

```bash
# Scoring Weights (must sum to 1.0)
FUNDAMENTAL_WEIGHT=0.6
SENTIMENT_WEIGHT=0.4

# Fundamental Thresholds
PE_RATIO_EXCELLENT=15
ROE_EXCELLENT=20
DEBT_TO_EQUITY_EXCELLENT=0.5

# Tracked Stocks
TRACKED_STOCKS=RELIANCE,TCS,INFY,HDFCBANK,ICICIBANK

# API Keys (optional)
NEWS_API_KEY=your_key_here
```

## 🧪 Testing

```bash
# Run all tests
poe test

# Run with coverage
poe test-cov

# Run specific test file
pytest tests/test_scoring.py -v
```

## 🚢 Deployment

### Local Development
```bash
poe docker-up
poe init-db
poe run-all-tasks
```

### Production (AWS)
1. Build images: `docker-compose build`
2. Push to ECR
3. Deploy with ECS/EKS
4. Use RDS for PostgreSQL
5. Use ElastiCache for Redis

## 📝 Available Poe Tasks

Run `poe` to see all available tasks:

```
format             - Format code with black and ruff
lint               - Run linting checks
test               - Run tests with pytest
test-cov           - Run tests with coverage
docker-up          - Start all Docker services
docker-down        - Stop all Docker services
docker-logs        - View Docker logs
init-db            - Initialize database
ingest-fundamentals - Run fundamental data ingestion
ingest-news        - Run news data ingestion
analyze-sentiment  - Analyze sentiment
compute-scores     - Compute composite scores
run-all-tasks      - Run full data pipeline
dev                - Run development server
shell              - Open IPython shell
clean              - Clean up generated files
```

## 🤝 Contributing

1. Install dev dependencies: `uv pip install -e ".[dev]"`
2. Format code: `poe format`
3. Run lints: `poe lint`
4. Run tests: `poe test`
5. Submit PR

## � License

MIT License - see LICENSE file

---

**Built with ⚡ modern Python tooling for Indian equity investors**
