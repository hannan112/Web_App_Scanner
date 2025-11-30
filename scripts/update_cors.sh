#!/bin/bash
# Script to update CORS configuration on Digital Ocean server

SSH_KEY="/home/hannan/keys/oceans_digital"
# Ensure we are in the project root
cd "$(dirname "$0")/.."
SERVER="root@143.198.211.182"
REMOTE_DIR="~/Web_App_Scanner"

echo "Updating CORS configuration..."

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER" << 'EOF'
cd ~/Web_App_Scanner

# Backup the .env file
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# Update CORS_ALLOWED_ORIGINS to include all three Vercel URLs and production domain (including api)
sed -i 's|CORS_ALLOWED_ORIGINS=.*|CORS_ALLOWED_ORIGINS=http://localhost:3000,https://morphbreak.site,https://www.morphbreak.site,https://api.morphbreak.site,https://web-app-scanner.vercel.app,https://web-app-scanner-git-main-hannan-alis-projects-0d0fd28d.vercel.app,https://web-app-scanner-iam4u58dg-hannan-alis-projects-0d0fd28d.vercel.app|' .env

# Update CSRF_TRUSTED_ORIGINS to include all three Vercel URLs and production domain (including api)
sed -i 's|CSRF_TRUSTED_ORIGINS=.*|CSRF_TRUSTED_ORIGINS=https://143.198.211.182.nip.io,https://morphbreak.site,https://www.morphbreak.site,https://api.morphbreak.site,https://web-app-scanner.vercel.app,https://web-app-scanner-git-main-hannan-alis-projects-0d0fd28d.vercel.app,https://web-app-scanner-iam4u58dg-hannan-alis-projects-0d0fd28d.vercel.app|' .env

# Update ALLOWED_HOSTS to ensure api.morphbreak.site is included
sed -i 's|ALLOWED_HOSTS=.*|ALLOWED_HOSTS=localhost,127.0.0.1,api.morphbreak.site,morphbreak.site,www.morphbreak.site,143.198.211.182|' .env

# Show the updated configuration
echo "Updated CORS configuration:"
echo "=========================="
grep -E "CORS_ALLOWED_ORIGINS|CSRF_TRUSTED_ORIGINS" .env
echo "=========================="

# Restart the backend service to apply changes
echo "Restarting backend service..."
if command -v docker-compose &> /dev/null; then
    docker-compose restart backend
elif command -v docker &> /dev/null && docker ps | grep -q backend; then
    docker restart $(docker ps | grep backend | awk '{print $1}')
else
    echo "Please restart your Django backend service manually to apply CORS changes"
fi

echo "Done!"
EOF

