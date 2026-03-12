#!/bin/bash

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         Adaptive Honeypot System Status                   ║"
echo "╚════════════════════════════════════════════════════════════╝"

echo ""
echo "📊 ORCHESTRATOR STATUS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
orchestrator_status=$(sudo docker ps --filter "name=orchestrator" --format "{{.Status}}")
if [ -n "$orchestrator_status" ]; then
    echo "✅ Orchestrator: $orchestrator_status"
else
    echo "❌ Orchestrator: NOT RUNNING"
fi

echo ""
echo "🍯 HONEYPOT CONTAINERS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

honeypots=$(sudo docker ps -a --filter "label=honeypot.id" --format "{{.Names}}")

if [ -z "$honeypots" ]; then
    echo "No honeypots deployed"
else
    for container in $honeypots; do
        echo ""
        echo "Container: $container"
        
        # Get status
        status=$(sudo docker inspect --format='{{.State.Status}}' "$container")
        if [ "$status" = "running" ]; then
            echo "  Status: ✅ $status"
        else
            echo "  Status: ❌ $status"
        fi
        
        # Get ports
        ports=$(sudo docker port "$container" 2>/dev/null)
        if [ -n "$ports" ]; then
            echo "  Ports: $ports"
        else
            echo "  Ports: None mapped"
        fi
        
        # Get honeypot ID
        hp_id=$(sudo docker inspect --format='{{index .Config.Labels "honeypot.id"}}' "$container")
        echo "  Honeypot ID: $hp_id"
        
        # Check if SSH is responding
        port=$(echo "$ports" | grep -oP '0.0.0.0:\K\d+' | head -1)
        if [ -n "$port" ]; then
            if timeout 2 bash -c "echo > /dev/tcp/127.0.0.1/$port" 2>/dev/null; then
                echo "  SSH Test: ✅ Port $port responding"
            else
                echo "  SSH Test: ❌ Port $port not responding"
                echo "  Last 5 log lines:"
                sudo docker logs --tail 5 "$container" 2>&1 | sed 's/^/    /'
            fi
        fi
    done
fi

echo ""
echo "🌐 NETWORK PORTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sudo netstat -tlnp 2>/dev/null | grep -E ":(2222|2223|1123|8000|3000)" | awk '{print $4, $7}' || echo "No honeypot ports found"

echo ""
echo "📈 SYSTEM RESOURCES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}')% used"
echo "Memory: $(free -h | awk '/^Mem:/ {print $3 "/" $2}')"
echo "Disk: $(df -h / | awk 'NR==2 {print $3 "/" $2 " (" $5 " used)"}')"

echo ""
echo "🔗 QUICK LINKS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Dashboard: http://localhost:3000"
echo "API Docs:  http://localhost:8000/docs"
echo "API Status: http://localhost:8000/status"

echo ""
echo "💡 QUICK COMMANDS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Fix system:        sudo ./fix_system.sh"
echo "Check logs:        sudo ./check_honeypots.sh"
echo "Restart all:       sudo docker-compose restart"
echo "View this status:  sudo ./status.sh"
