#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}[START]${NC} $*"; }
err() { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }

[ -f .env ] || err ".env не найден. Сначала запустите ./install.sh"

command -v docker >/dev/null 2>&1 || err "docker не найден"
docker compose version >/dev/null 2>&1 || err "docker compose не найден"

log "Запуск контейнеров..."
docker compose up -d

log "Готово!"
echo ""
echo "  API: http://localhost:8000"
echo "  DB:  localhost:5433"
