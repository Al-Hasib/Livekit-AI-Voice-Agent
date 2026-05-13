#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Setting up Voice Agent project..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# ── Check dependencies ─────────────────────────────────────────
check_cmd() {
    if ! command -v "$1" &>/dev/null; then
        echo "❌ $1 is not installed. Please install it first."
        echo "   → $2"
        exit 1
    fi
}

check_cmd python3 "https://www.python.org/downloads/"
check_cmd node "https://nodejs.org/"
check_cmd docker "https://docs.docker.com/get-docker/"
check_cmd docker-compose "https://docs.docker.com/compose/install/"

echo "✅ All dependencies found"

# ── Backend setup ──────────────────────────────────────────────
echo ""
echo "📦 Setting up backend..."
cd "$PROJECT_ROOT/backend"

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Backend dependencies installed"

# ── Frontend setup ─────────────────────────────────────────────
echo ""
echo "📦 Setting up frontend..."
cd "$PROJECT_ROOT/frontend"

npm install

echo "✅ Frontend dependencies installed"

# ── Environment file ──────────────────────────────────────────
echo ""
ENV_FILE="$PROJECT_ROOT/infra/docker/.env"
if [ ! -f "$ENV_FILE" ]; then
    cp "$PROJECT_ROOT/infra/docker/.env.example" "$ENV_FILE"
    echo "⚠️  Created .env file at $ENV_FILE"
    echo "   Please fill in your API keys before running."
else
    echo "✅ .env file already exists"
fi

# ── Uploads directory ─────────────────────────────────────────
mkdir -p "$PROJECT_ROOT/backend/uploads"

echo ""
echo "🎉 Setup complete! Next steps:"
echo ""
echo "   1. Edit infra/docker/.env with your API keys"
echo "   2. Start services:"
echo "      cd infra/docker && docker-compose up -d"
echo ""
echo "   Or run locally:"
echo "      Backend:  cd backend && source .venv/bin/activate && python -m app.main"
echo "      Agent:    cd backend && source .venv/bin/activate && python agent_worker.py"
echo "      Frontend: cd frontend && npm run dev"