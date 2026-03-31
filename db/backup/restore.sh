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

DB_HOST="${db_host:-localhost}"
DB_PORT="${db_port:-5433}"
DB_USER="${db_user:-admin}"
DB_PASS="${db_pass:-root}"
DB_NAME="${db_name:-postgres}"

RESOURCES_DIR="${PROJECT_DIR}/db/resources"

echo "=== RoboFactory Restore ==="
echo ""

if [ -z "$1" ]; then
    echo "Usage: $0 <backup_name>"
    echo ""
    echo "Available backups:"
    if [ -d "${BACKUP_DIR}" ]; then
        ls -1 "${BACKUP_DIR}" | grep -E "^backup_" | while read backup; do
            echo "  - ${backup}"
        done
    else
        echo "  No backups found in ${BACKUP_DIR}"
    fi
    exit 1
fi

BACKUP_NAME="$1"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

if [ ! -d "${BACKUP_PATH}" ]; then
    echo "Error: Backup '${BACKUP_NAME}' not found"
    exit 1
fi

if [ ! -f "${BACKUP_PATH}/database.dump" ]; then
    echo "Error: database.dump not found in backup"
    exit 1
fi

echo "Found backup: ${BACKUP_NAME}"
echo ""

read -p "WARNING: This will overwrite current database and resources. Continue? (yes/no): " CONFIRM
if [ "${CONFIRM}" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

echo ""
echo "[1/3] Restoring database..."
export PGPASSWORD="${DB_PASS}"
pg_restore -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" --clean --if-exists -v "${BACKUP_PATH}/database.dump"
echo "Database restore completed."

echo "[2/3] Restoring resources..."
if [ -f "${BACKUP_PATH}/resources.tar.gz" ]; then
    rm -rf "${RESOURCES_DIR}"
    tar -xzf "${BACKUP_PATH}/resources.tar.gz" -C "$(dirname ${RESOURCES_DIR})"
    echo "Resources restore completed."
else
    echo "Warning: resources.tar.gz not found in backup, skipping..."
fi

echo "[3/3] Verifying restore..."
if [ -d "${RESOURCES_DIR}" ]; then
    RESOURCE_COUNT=$(ls -1 "${RESOURCES_DIR}" 2>/dev/null | wc -l)
    echo "Resources restored: ${RESOURCE_COUNT} items"
fi

echo ""
echo "=== Restore completed successfully ==="