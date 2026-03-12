#!/bin/bash

echo "🔧 Complete Fix for Volume Path Issue"
echo "======================================"
echo ""

# Check if running with sudo
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  Please run with sudo:"
    echo "   sudo ./complete_fix.sh"
    exit 1
fi

echo "1️⃣  Stopping orchestrator..."
docker-compose stop orchestrator

echo "2️⃣  Removing old container..."
docker-compose rm -f orchestrator

echo "3️⃣  Removing old image to force rebuild..."
docker rmi adaptive_honeypot-orchestrator 2>/dev/null || true

echo "4️⃣  Clearing Docker build cache..."
docker builder prune -f

echo "5️⃣  Rebuilding with no cache..."
docker-compose build --no-cache orchestrator

echo "6️⃣  Starting new container..."
docker-compose up -d orchestrator

echo ""
echo "⏳ Waiting for container to start..."
sleep 5

echo ""
echo "📊 Container status:"
docker-compose ps orchestrator

echo ""
echo "📝 Recent logs:"
docker-compose logs --tail=30 orchestrator

echo ""
echo "======================================"
echo "✅ Fix applied!"
echo ""
echo "🧪 Test deployment:"
echo "   curl -X POST http://localhost:8000/honeypots/deploy \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"name\": \"test\", \"port\": 2222}'"
echo ""
echo "📝 Watch logs:"
echo "   docker-compose logs -f orchestrator"
echo "======================================"
