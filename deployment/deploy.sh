#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Deployment Process...${NC}"

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Docker not found. Installing Docker...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    sudo usermod -aG docker $USER
    echo -e "${GREEN}Docker installed. Please log out and log back in for group changes to take effect.${NC}"
    exit 1
fi

# Pull latest changes
echo -e "${YELLOW}📥 Pulling latest code...${NC}"
git pull origin main

# Build and start containers
echo -e "${YELLOW}🏗️ Building and starting containers...${NC}"
docker compose -f deployment/docker-compose.prod.yml up -d --build

# Run migrations
echo -e "${YELLOW}🔄 Running database migrations...${NC}"
docker compose -f deployment/docker-compose.prod.yml exec backend python manage.py migrate

# Collect static files
echo -e "${YELLOW}🎨 Collecting static files...${NC}"
docker compose -f deployment/docker-compose.prod.yml exec backend python manage.py collectstatic --noinput

# Clean up unused images
echo -e "${YELLOW}🧹 Cleaning up old images...${NC}"
docker system prune -f

echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo -e "Backend is running at: http://$(curl -s ifconfig.me):8000"
