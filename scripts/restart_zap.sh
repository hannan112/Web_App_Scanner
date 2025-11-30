#!/bin/bash

# Script to restart only the ZAP container
# Useful for clearing stuck scans or resetting ZAP state

# Ensure we are in the project root
cd "$(dirname "$0")/.."

CONTAINER_NAME="security_scanner_zap"

echo "Restarting ZAP container ($CONTAINER_NAME)..."

if docker restart "$CONTAINER_NAME"; then
    echo "✅ Successfully restarted $CONTAINER_NAME"
else
    echo "❌ Failed to restart $CONTAINER_NAME"
    exit 1
fi

echo "ZAP restart process completed."
