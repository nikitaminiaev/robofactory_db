#!/usr/bin/env bash
# Сборка RoboFactory-DB в AppImage.
#
# Использование:
#   ./packaging/build_appimage.sh
#   PLMPLUGIN_SRC=/путь/до/PLMplugin ./packaging/build_appimage.sh   # свой путь к плагину
#
# Результат: dist/RoboFactory-DB-x86_64.AppImage
# Зависимости сборки: bash, rsync, curl, docker не нужен.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PACKAGING_DIR="$PROJECT_DIR/packaging"
PLMPLUGIN_SRC="${PLMPLUGIN_SRC:-/media/ssd_1_9tb/PycharmProjects/freecadPlugin/PLMplugin}"
BUILD_DIR="$PROJECT_DIR/build"
APPDIR="$BUILD_DIR/AppDir"
DIST_DIR="$PROJECT_DIR/dist"
TOOLS_DIR="$BUILD_DIR/tools"
APPIMAGETOOL_URL="https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage"
OUTPUT="$DIST_DIR/RoboFactory-DB-x86_64.AppImage"

log() { printf '[BUILD] %s\n' "$*"; }
die() { printf '[BUILD] ОШИБКА: %s\n' "$*" >&2; exit 1; }

check_prerequisites() {
    [ -f "$PROJECT_DIR/api/main.py" ] || die "не найден $PROJECT_DIR/api/main.py — запускайте из проекта robofactory_db"
    [ -d "$PLMPLUGIN_SRC" ] || die "PLMplugin не найден: $PLMPLUGIN_SRC (переопределите: PLMPLUGIN_SRC=/путь/до/PLMplugin $0)"
    command -v rsync >/dev/null 2>&1 || die "rsync не найден"
    command -v curl >/dev/null 2>&1 || die "curl не найден"
}

prepare_appdir() {
    log "Сборка AppDir: $APPDIR"
    rm -rf "$APPDIR"
    mkdir -p "$APPDIR" "$DIST_DIR" "$TOOLS_DIR"

    log "Копирую код проекта (api, docker)..."
    rsync -a \
        --exclude '__pycache__' \
        --exclude '.pytest_cache' \
        --exclude 'tests' \
        --exclude 'resources' \
        "$PROJECT_DIR/api" "$APPDIR/"
    rsync -a "$PROJECT_DIR/docker" "$APPDIR/"
    # Внутри AppDir подменяем requirements.txt на lock-файл с зафиксированными версиями
    # (см. комментарий в requirements.app.txt) — dev-файл проекта не трогаем.
    cp "$PACKAGING_DIR/requirements.app.txt" "$APPDIR/docker/api/requirements.txt"
    cp "$PROJECT_DIR/.env.example" "$APPDIR/"
    cp "$PACKAGING_DIR/docker-compose.app.yaml" "$APPDIR/"
    cp "$PACKAGING_DIR/VERSION" "$APPDIR/"

    log "Копирую PLMplugin из $PLMPLUGIN_SRC ..."
    # ВАЖНО: trailing slash на источнике — копируется СОДЕРЖИМОЕ каталога
    # (без слэша rsync копирует каталог ВНУТРЬ dest: AppDir/PLMplugin/PLMplugin)
    rsync -a --exclude '__pycache__' "$PLMPLUGIN_SRC/" "$APPDIR/PLMplugin/"

    log "Копирую метаданные AppImage (AppRun, .desktop, иконка)..."
    install -m 755 "$PACKAGING_DIR/AppRun" "$APPDIR/AppRun"
    cp "$PACKAGING_DIR/robofactory-db.desktop" "$APPDIR/"
    cp "$PACKAGING_DIR/robofactory-db.png" "$APPDIR/"
}

ensure_appimagetool() {
    if command -v appimagetool >/dev/null 2>&1; then
        APPIMAGETOOL="appimagetool"
        return 0
    fi
    local tool="$TOOLS_DIR/appimagetool-x86_64.AppImage"
    if [ ! -x "$tool" ]; then
        log "Скачиваю appimagetool..."
        curl -fL "$APPIMAGETOOL_URL" -o "$tool" || die "не удалось скачать appimagetool: $APPIMAGETOOL_URL"
        chmod +x "$tool"
    fi
    APPIMAGETOOL="$tool"
}

build_appimage() {
    log "Собираю AppImage: $OUTPUT"
    rm -f "$OUTPUT"
    ARCH=x86_64 APPIMAGE_EXTRACT_AND_RUN=1 "$APPIMAGETOOL" "$APPDIR" "$OUTPUT" \
        || die "appimagetool завершился с ошибкой"
    log "Готово: $OUTPUT"
    log "Проверка: запуск с выводом статуса"
    "$OUTPUT" --status || true
}

main() {
    check_prerequisites
    prepare_appdir
    ensure_appimagetool
    build_appimage
}

main "$@"
