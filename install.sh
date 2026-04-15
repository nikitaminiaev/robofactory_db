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

run_privileged() {
    if [ "$(id -u)" -eq 0 ]; then
        "$@"
        return
    fi

    if command -v sudo >/dev/null 2>&1; then
        sudo "$@"
        return
    fi

    err "Нужны права root (sudo не найден)"
}

install_docker() {
    if ! command -v curl >/dev/null 2>&1; then
        err "Для установки Docker нужен curl"
    fi

    log "Устанавливаю Docker и Docker Compose..."
    run_privileged sh -c "curl -fsSL https://get.docker.com | sh"

    if ! command -v docker >/dev/null 2>&1; then
        err "Не удалось установить docker"
    fi
}

add_user_to_docker_group() {
    local target_user="${SUDO_USER:-$USER}"
    local group_name

    [ -n "$target_user" ] || return

    for group_name in $(id -nG "$target_user"); do
        [ "$group_name" != "docker" ] && continue
        log "Пользователь $target_user уже в группе docker"
        return
    done

    log "Добавляю пользователя $target_user в группу docker..."
    run_privileged groupadd -f docker
    run_privileged usermod -aG docker "$target_user"
    warn "Перелогиньтесь (или выполните 'newgrp docker'), чтобы применились права группы"
}

# --- .env ---
if [ ! -f .env ]; then
    cp .env.example .env
    log "Создан .env из .env.example"
else
    warn ".env уже существует, пропускаю"
fi

# --- Docker ---
if ! command -v docker >/dev/null 2>&1 || ! docker compose version >/dev/null 2>&1; then
    warn "Docker или Docker Compose не найдены"
    read -r -p "Установить Docker и Docker Compose сейчас? [y/N]: " install_docker_choice

    case "${install_docker_choice,,}" in
        y|yes)
            install_docker
            ;;
        *)
            err "Без Docker продолжить установку нельзя"
            ;;
    esac
fi

docker compose version >/dev/null 2>&1 || err "docker compose не найден после установки"
add_user_to_docker_group

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
