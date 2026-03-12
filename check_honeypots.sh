#!/bin/bash

echo "=== Honeypot Containers Status ==="
sudo docker ps -a --filter "label=honeypot.id" --format "table {{.Names}}\t{{.ID}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "=== Checking Container Logs ==="
for container in $(sudo docker ps -a --filter "label=honeypot.id" --format "{{.Names}}"); do
    echo ""
    echo "--- Logs for $container ---"
    sudo docker logs --tail 20 "$container" 2>&1
done

echo ""
echo "=== Network Ports ==="
sudo netstat -tlnp | grep -E ":(2222|2223|1123)" || echo "No honeypot ports listening"
