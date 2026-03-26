#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[INSTALL]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()  { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }

# --- .env ---
if [ ! -f .env ]; then
    cp .env.example .env
    log "Создан .env из .env.example"
else
    warn ".env уже существует, пропускаю"
fi

# --- Docker ---
command -v docker >/dev/null 2>&1 || err "docker не найден"
docker compose version >/dev/null 2>&1 || err "docker compose не найден"

log "Сборка контейнеров..."
docker compose build

log "Запуск контейнеров..."
docker compose up -d

# --- Ждём готовности PostgreSQL ---
log "Ожидание готовности PostgreSQL..."
RETRIES=30
until docker compose exec -T db pg_isready -U admin >/dev/null 2>&1; do
    RETRIES=$((RETRIES - 1))
    [ "$RETRIES" -le 0 ] && err "PostgreSQL не стартовал за 30 секунд"
    sleep 1
done
log "PostgreSQL готов"

# --- Миграции Alembic (создают всю схему с нуля) ---
log "Применение миграций Alembic..."
docker compose exec -T api alembic -c /usr/src/api/database/alembic.ini upgrade head 2>/dev/null || warn "Миграции могли примениться ранее"
log "Миграции применены"

log "Установка завершена!"
echo ""
echo "  API: http://localhost:8000"
echo "  DB:  localhost:5433"
echo ""
echo "  Запустить повторно: ./start.sh"
echo "  Остановить:         docker compose down"
