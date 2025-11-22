#!/bin/bash
# Script to deploy all changes to both Vercel (frontend) and Digital Ocean (backend)

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SSH_KEY="/home/hannan/keys/oceans_digital"
SERVER="root@143.198.211.182"
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

# Step 3: Commit changes
echo -e "${YELLOW}📝 Committing changes...${NC}"
git add -A
git commit -m "Fix: Improve scan status polling and CORS configuration

- Add 30s timeout to API client for production
- Improve error handling to distinguish network errors from scan failures
- Add retry logic with exponential backoff for failed requests
- Make polling more resilient - continue after temporary failures
- Improve CORS configuration parsing to handle whitespace
- Add debug logging for CORS origins"

# Step 4: Push to git (this will trigger Vercel deployment)
echo -e "${YELLOW}📤 Pushing to git (triggers Vercel auto-deploy)...${NC}"
git push origin main

echo -e "${GREEN}✅ Frontend changes pushed! Vercel will auto-deploy.${NC}"
echo ""

# Step 5: Deploy backend to Digital Ocean
echo -e "${YELLOW}🌊 Deploying backend to Digital Ocean...${NC}"
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER" << 'EOF'
cd ~/Web_App_Scanner

# Backup current .env
echo "📦 Backing up .env file..."
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# Update CORS_ALLOWED_ORIGINS to include all three Vercel URLs
echo "🔧 Updating CORS configuration..."
sed -i 's|CORS_ALLOWED_ORIGINS=.*|CORS_ALLOWED_ORIGINS=http://localhost:3000,https://web-app-scanner.vercel.app,https://web-app-scanner-git-main-hannan-alis-projects-0d0fd28d.vercel.app,https://web-app-scanner-iam4u58dg-hannan-alis-projects-0d0fd28d.vercel.app|' .env

# Update CSRF_TRUSTED_ORIGINS to include all three Vercel URLs
sed -i 's|CSRF_TRUSTED_ORIGINS=.*|CSRF_TRUSTED_ORIGINS=https://143.198.211.182.nip.io,https://web-app-scanner.vercel.app,https://web-app-scanner-git-main-hannan-alis-projects-0d0fd28d.vercel.app,https://web-app-scanner-iam4u58dg-hannan-alis-projects-0d0fd28d.vercel.app|' .env

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

