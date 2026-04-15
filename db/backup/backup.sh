#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "${SCRIPT_DIR}")"
ENV_FILE="${PROJECT_DIR}/.env"

if [ -f "${ENV_FILE}" ]; then
    set -a
    source "${ENV_FILE}"
    set +a
fi

BACKUP_DIR="${BACKUP_DIR:-/media/ssd_1_9tb/PycharmProjects/robofactory_db/db/backup}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="backup_${TIMESTAMP}"

DB_HOST="${db_host:-localhost}"
DB_PORT="${db_port:-5433}"
DB_USER="${db_user:-admin}"
DB_PASS="${db_pass:-root}"
DB_NAME="${db_name:-postgres}"

RESOURCES_DIR="${PROJECT_DIR}/db/resources"
STORAGE_DIR="${PROJECT_DIR}/db/storage"

echo "=== RoboFactory Backup ==="
echo "Timestamp: ${TIMESTAMP}"
echo ""

mkdir -p "${BACKUP_DIR}/${BACKUP_NAME}"

echo "[1/3] Backing up database..."
export PGPASSWORD="${DB_PASS}"
pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -F c -b -v -f "${BACKUP_DIR}/${BACKUP_NAME}/database.dump"
echo "Database backup completed: ${BACKUP_DIR}/${BACKUP_NAME}/database.dump"

echo "[2/3] Backing up resources (CAD files and git repositories)..."
if [ -d "${RESOURCES_DIR}" ]; then
    tar -czf "${BACKUP_DIR}/${BACKUP_NAME}/resources.tar.gz" -C "$(dirname ${RESOURCES_DIR})" "$(basename ${RESOURCES_DIR})"
    echo "Resources backup completed: ${BACKUP_DIR}/${BACKUP_NAME}/resources.tar.gz"
else
    echo "Warning: Resources directory not found, skipping..."
fi

echo "[3/3] Creating manifest..."
cat > "${BACKUP_DIR}/${BACKUP_NAME}/manifest.txt" << EOF
RoboFactory Backup Manifest
=============================
Timestamp: ${TIMESTAMP}
Created: $(date -u +"%Y-%m-%d %H:%M:%S UTC")

Components:
- database.dump (PostgreSQL custom format)
- resources.tar.gz (CAD files and git repositories)

Database connection:
- Host: ${DB_HOST}
- Port: ${DB_PORT}
- User: ${DB_USER}
- Database: ${DB_NAME}
EOF
echo "Manifest created."

echo ""
echo "=== Backup completed successfully ==="
echo "Backup location: ${BACKUP_DIR}/${BACKUP_NAME}/"
echo ""

BACKUP_SIZE=$(du -sh "${BACKUP_DIR}/${BACKUP_NAME}" | cut -f1)
echo "Backup size: ${BACKUP_SIZE}"