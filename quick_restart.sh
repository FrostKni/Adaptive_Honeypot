#!/bin/bash
echo "🔄 Restarting orchestrator with volume fix..."
docker-compose up -d --build orchestrator
echo "✅ Done! Check logs:"
echo "   docker-compose logs -f orchestrator"
