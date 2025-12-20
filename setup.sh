#!/usr/bin/env bash
set -e

echo "🚀 Personal Stock Screener - Quick Setup"
echo "========================================="
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed"
    echo "📦 Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo "✅ uv installed successfully"
    echo "⚠️  Please restart your terminal and run this script again"
    exit 0
fi

echo "✅ uv is installed"
echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
uv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies with uv (this is fast!)..."
uv pip install -e ".[dev]"

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Copy .env.example to .env:"
echo "     cp .env.example .env"
echo ""
echo "  2. Edit .env with your configuration:"
echo "     nano .env"
echo ""
echo "  3. Start Docker services:"
echo "     poe docker-up"
echo ""
echo "  4. Initialize database:"
echo "     poe init-db"
echo ""
echo "  5. Run data pipeline:"
echo "     poe run-all-tasks"
echo ""
echo "  6. Access API docs:"
echo "     http://localhost:8000/docs"
echo ""
echo "Run 'poe' to see all available tasks!"
