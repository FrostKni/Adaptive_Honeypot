#!/bin/bash

echo "=== Fixing Adaptive Honeypot System ==="

cd /run/media/asta/HD/CYBER_SECURITY/Project/Adaptive_Honeypot

echo ""
echo "Step 1: Restarting orchestrator container..."
sudo docker-compose restart orchestrator

echo ""
echo "Step 2: Waiting for orchestrator to start..."
sleep 5

echo ""
echo "Step 3: Checking honeypot containers..."
sudo docker ps -a --filter "label=honeypot.id" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "Step 4: Checking for crashed containers..."
crashed=$(sudo docker ps -a --filter "label=honeypot.id" --filter "status=exited" --format "{{.Names}}")

if [ -n "$crashed" ]; then
    echo "Found crashed containers, restarting them..."
    for container in $crashed; do
        echo "Restarting $container..."
        sudo docker restart "$container"
    done
else
    echo "No crashed containers found."
fi

echo ""
echo "Step 5: Checking container logs for errors..."
for container in $(sudo docker ps --filter "label=honeypot.id" --format "{{.Names}}"); do
    echo ""
    echo "--- Last 10 lines of $container ---"
    sudo docker logs --tail 10 "$container" 2>&1 | grep -i "error\|fail\|exception" || echo "No errors found"
done

echo ""
echo "=== Fix Complete ==="
echo "Dashboard: http://localhost:3000"
echo "API: http://localhost:8000/docs"
