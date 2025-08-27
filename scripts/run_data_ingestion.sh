#!/bin/bash
#
# Standalone Data Ingestion Runner
# For scheduled execution (systemd, cron, N8n, etc.)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Configuration
CONTAINER_NAME="aslan_data_ingestion_$(date +%Y%m%d_%H%M%S)"
IMAGE_NAME="aslan_drive_data_ingestion:latest"
NETWORK_NAME="aslan_network"
LOG_FILE="/var/log/aslan/data_ingestion_$(date +%Y%m%d).log"

# Environment variables
DATABASE_URL="${DATABASE_URL:-postgresql://trader:trading123@aslan_postgres:5432/aslan_drive}"
LOG_LEVEL="${LOG_LEVEL:-info}"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Create log directory if it doesn't exist
sudo mkdir -p "$(dirname "$LOG_FILE")"

log "Starting data ingestion job..."
log "Container: $CONTAINER_NAME"
log "Image: $IMAGE_NAME"
log "Network: $NETWORK_NAME"

# Check if network exists
if ! docker network inspect "$NETWORK_NAME" >/dev/null 2>&1; then
    log "ERROR: Network $NETWORK_NAME does not exist. Infrastructure may not be running."
    exit 1
fi

# Check if database is reachable
if ! docker run --rm --network "$NETWORK_NAME" \
    -e PGPASSWORD="${POSTGRES_PASSWORD:-trading123}" \
    postgres:15 \
    pg_isready -h aslan_postgres -p 5432 -U trader -d aslan_drive; then
    log "ERROR: Database is not reachable"
    exit 1
fi

log "Database connectivity confirmed"

# Run data ingestion container
log "Starting data ingestion container..."

docker run \
    --name "$CONTAINER_NAME" \
    --network "$NETWORK_NAME" \
    --rm \
    -e DATABASE_URL="$DATABASE_URL" \
    -e LOG_LEVEL="$LOG_LEVEL" \
    -e CONTINUOUS_MODE=false \
    "$IMAGE_NAME" 2>&1 | tee -a "$LOG_FILE"

EXIT_CODE=${PIPESTATUS[0]}

if [ $EXIT_CODE -eq 0 ]; then
    log "Data ingestion completed successfully"
else
    log "ERROR: Data ingestion failed with exit code $EXIT_CODE"
    exit $EXIT_CODE
fi

# Cleanup old log files (keep last 7 days)
find "$(dirname "$LOG_FILE")" -name "data_ingestion_*.log" -mtime +7 -delete 2>/dev/null || true

log "Data ingestion job finished"