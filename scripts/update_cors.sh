#!/bin/bash
# Script to update CORS configuration on Digital Ocean server

SSH_KEY="${DEPLOY_SSH_KEY:?Set DEPLOY_SSH_KEY to your SSH private key path}"
# Ensure we are in the project root
cd "$(dirname "$0")/.."
SERVER="${DEPLOY_SERVER:?Set DEPLOY_SERVER, e.g. root@your-server-ip}"
PROD_DOMAIN="${DEPLOY_DOMAIN:?Set DEPLOY_DOMAIN, e.g. api.your-domain.com}"
FRONTEND_ORIGINS="${DEPLOY_FRONTEND_ORIGINS:?Set DEPLOY_FRONTEND_ORIGINS, comma-separated allowed origins}"
REMOTE_DIR="~/Web_App_Scanner"

echo "Updating CORS configuration..."

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER" bash -s -- "$FRONTEND_ORIGINS" "$PROD_DOMAIN" << 'EOF'
cd ~/Web_App_Scanner
FRONTEND_ORIGINS="$1"
PROD_DOMAIN="$2"

# Backup the .env file
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# Update CORS_ALLOWED_ORIGINS / CSRF_TRUSTED_ORIGINS / ALLOWED_HOSTS
sed -i "s|CORS_ALLOWED_ORIGINS=.*|CORS_ALLOWED_ORIGINS=http://localhost:3000,${FRONTEND_ORIGINS}|" .env
sed -i "s|CSRF_TRUSTED_ORIGINS=.*|CSRF_TRUSTED_ORIGINS=${FRONTEND_ORIGINS}|" .env
sed -i "s|ALLOWED_HOSTS=.*|ALLOWED_HOSTS=localhost,127.0.0.1,${PROD_DOMAIN}|" .env

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

