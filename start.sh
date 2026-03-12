#!/bin/bash

echo "🍯 Adaptive Honeypot System - Startup Script"
echo "=============================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.example .env
    echo "✅ Please edit .env file and add your API keys"
    echo "   nano .env"
    exit 1
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs honeypots/cowrie

# Pull Cowrie image
echo "🐳 Pulling Cowrie honeypot image..."
docker pull cowrie/cowrie:latest

# Build and start services
echo "🚀 Starting Adaptive Honeypot System..."
docker-compose up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 5

# Check status
echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "✅ Adaptive Honeypot System is running!"
echo ""
echo "🌐 Access Points:"
echo "   Dashboard: http://localhost:3000"
echo "   API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📝 Useful Commands:"
echo "   View logs: docker-compose logs -f"
echo "   Stop system: docker-compose down"
echo "   Restart: docker-compose restart"
echo ""
