#!/bin/bash
# Script to deploy all changes to both Vercel (frontend) and Digital Ocean (backend)

set -e

# Ensure we are in the project root
cd "$(dirname "$0")/.."

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SSH_KEY="${DEPLOY_SSH_KEY:?Set DEPLOY_SSH_KEY to your SSH private key path}"
SERVER="${DEPLOY_SERVER:?Set DEPLOY_SERVER, e.g. root@your-server-ip}"
PROD_DOMAIN="${DEPLOY_DOMAIN:?Set DEPLOY_DOMAIN, e.g. api.your-domain.com}"
FRONTEND_ORIGINS="${DEPLOY_FRONTEND_ORIGINS:?Set DEPLOY_FRONTEND_ORIGINS, comma-separated allowed origins}"
REMOTE_DIR="~/Web_App_Scanner"

echo -e "${BLUE}🚀 Starting Deployment Process...${NC}"
echo ""

# Step 1: Show what files have changed
echo -e "${YELLOW}📋 Changed files:${NC}"
git status --short
echo ""

# Step 2: Ask for confirmation
read -p "Do you want to commit and push these changes? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 1
fi

# Step 3: Require changes to already be committed - this script should not
# invent commit messages on your behalf
if [[ -n "$(git status --porcelain)" ]]; then
    echo "Error: You have uncommitted changes. Commit them yourself first, then re-run this script."
    exit 1
fi

# Step 4: Push to git (this will trigger Vercel deployment)
echo -e "${YELLOW}📤 Pushing to git (triggers Vercel auto-deploy)...${NC}"
git push origin main

echo -e "${GREEN}✅ Frontend changes pushed! Vercel will auto-deploy.${NC}"
echo ""

# Step 5: Deploy backend to Digital Ocean
echo -e "${YELLOW}🌊 Deploying backend to Digital Ocean...${NC}"
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER" bash -s -- "$FRONTEND_ORIGINS" "$PROD_DOMAIN" << 'EOF'
cd ~/Web_App_Scanner
FRONTEND_ORIGINS="$1"
PROD_DOMAIN="$2"

# Backup current .env
echo "📦 Backing up .env file..."
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# Update CORS_ALLOWED_ORIGINS / CSRF_TRUSTED_ORIGINS / ALLOWED_HOSTS
echo "🔧 Updating CORS configuration..."
sed -i "s|CORS_ALLOWED_ORIGINS=.*|CORS_ALLOWED_ORIGINS=http://localhost:3000,${FRONTEND_ORIGINS}|" .env
sed -i "s|CSRF_TRUSTED_ORIGINS=.*|CSRF_TRUSTED_ORIGINS=${FRONTEND_ORIGINS}|" .env
sed -i "s|ALLOWED_HOSTS=.*|ALLOWED_HOSTS=localhost,127.0.0.1,${PROD_DOMAIN}|" .env

# Show updated configuration
echo "✅ Updated CORS configuration:"
grep -E "CORS_ALLOWED_ORIGINS|CSRF_TRUSTED_ORIGINS" .env
echo ""

# Pull latest code
echo "📥 Pulling latest code from git..."
git pull origin main

# Rebuild and restart backend container
echo "🏗️ Rebuilding backend container..."
if command -v docker-compose &> /dev/null; then
    docker-compose -f deployment/docker-compose.prod.yml up -d --build backend
    echo "✅ Backend container rebuilt and restarted"
elif command -v docker &> /dev/null; then
    # If using docker directly
    docker build -f deployment/Dockerfile -t security_scanner_backend .
    docker restart security_scanner_backend || echo "⚠️ Container might need to be started manually"
else
    echo "⚠️ Docker not found. Please restart your backend service manually."
fi

echo ""
echo "✅ Backend deployment complete!"
EOF

echo ""
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo ""
echo "Summary:"
echo "  ✅ Frontend: Pushed to git, Vercel will auto-deploy"
echo "  ✅ Backend: Deployed to Digital Ocean"
echo "  ✅ CORS: Updated with all three Vercel URLs"
echo ""
echo "Next steps:"
echo "  1. Wait for Vercel to finish deploying (check Vercel dashboard)"
echo "  2. Test the scan status page on your Vercel URL"
echo "  3. Verify CORS is working by checking browser console for errors"

