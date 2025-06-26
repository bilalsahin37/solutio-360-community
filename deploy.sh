#!/bin/bash

# Solutio 360 - Production Deployment Script
# Usage: ./deploy.sh

echo "🚀 Starting Solutio 360 deployment..."

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Docker if not exists
if ! command -v docker &> /dev/null; then
    echo "🐳 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
fi

# Install Docker Compose if not exists
if ! command -v docker-compose &> /dev/null; then
    echo "🐳 Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Install Certbot for SSL
echo "🔒 Installing Certbot..."
sudo apt install certbot python3-certbot-nginx -y

# Clone/Update repository
if [ ! -d "solutio_360" ]; then
    echo "📥 Cloning repository..."
    git clone https://github.com/bilalsahin37/solutio-360-community.git solutio_360
    cd solutio_360
else
    echo "🔄 Updating repository..."
    cd solutio_360
    git pull origin main
fi

# Build and start containers
echo "🏗️ Building Docker containers..."
docker-compose -f docker-compose.production.yml build

echo "▶️ Starting services..."
docker-compose -f docker-compose.production.yml up -d

# Get SSL certificate
echo "🔒 Setting up SSL certificate..."
sudo certbot --nginx -d www.solutio360.net -d solutio360.net --non-interactive --agree-tos --email bilal@solutio360.net

# Restart nginx with SSL
docker-compose -f docker-compose.production.yml restart nginx

echo "✅ Deployment completed!"
echo "🌐 Your site should be live at: https://www.solutio360.net"
echo "📧 Admin email: bilal@solutio360.net"

# Show running containers
echo "📊 Running containers:"
docker-compose -f docker-compose.production.yml ps 