#!/bin/bash
# Script to sync production database to local environment

# Configuration
# Ensure we are in the project root
cd "$(dirname "$0")/.."

SSH_KEY="/home/hannan/keys/oceans_digital"
SERVER="root@143.198.211.182"
REMOTE_DB_PATH="/root/Web_App_Scanner/backend/db.sqlite3"
LOCAL_DB_PATH="backend/db.sqlite3"
BACKUP_DIR="backend/backups"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting database sync from production...${NC}"

# Ensure we are in the project root
if [ ! -d "backend" ]; then
    echo -e "${RED}Error: Please run this script from the project root directory.${NC}"
    exit 1
fi

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Backup local database
if [ -f "$LOCAL_DB_PATH" ]; then
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/db.sqlite3.backup.$TIMESTAMP"
    echo -e "Backing up local database to ${GREEN}$BACKUP_FILE${NC}..."
    cp "$LOCAL_DB_PATH" "$BACKUP_FILE"
else
    echo -e "${YELLOW}No local database found to backup.${NC}"
fi

# Download production database
echo -e "Downloading database from production (${SERVER})..."
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER:$REMOTE_DB_PATH" "$LOCAL_DB_PATH"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Database synced successfully!${NC}"
    echo -e "${YELLOW}Note: You may need to restart your local server to see the changes.${NC}"
else
    echo -e "${RED}Failed to download database from production.${NC}"
    # Restore backup if download failed
    if [ -f "$BACKUP_FILE" ]; then
        echo -e "Restoring backup..."
        cp "$BACKUP_FILE" "$LOCAL_DB_PATH"
    fi
    exit 1
fi
