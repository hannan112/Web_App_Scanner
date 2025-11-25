#!/bin/bash

# Define container names
CONTAINERS=("security_scanner_backend" "security_scanner_zap" "security_scanner_db")

echo "Restarting containers: ${CONTAINERS[*]}..."

# Loop through and restart each container
for container in "${CONTAINERS[@]}"; do
    if docker restart "$container"; then
        echo "Successfully restarted $container"
    else
        echo "Failed to restart $container"
    fi
done

echo "Restart process completed."
