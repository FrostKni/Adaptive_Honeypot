# Deployment Guide

## Prerequisites

- Docker 24.0+
- Docker Compose 2.20+
- Kubernetes 1.28+ (for production)
- kubectl configured
- Helm 3.0+ (optional)

## Quick Deployment (Docker Compose)

### 1. Configure Environment

```bash
# Clone repository
git clone https://github.com/FrostKni/Adaptive_Honeypot.git
cd Adaptive_Honeypot

# Copy and edit environment file
cp .env.example .env
nano .env
```

Required environment variables:
```bash
# AI Provider
AI_PROVIDER=openai
OPENAI_API_KEY=sk-your-key

# Database
DB_PASSWORD=secure_password

# Security
SECURITY_JWT_SECRET=your-jwt-secret

# Alerting (optional)
ALERT_SLACK_WEBHOOK_URL=https://hooks.slack.com/...
```

### 2. Deploy Services

```bash
# Start all services
docker-compose -f deploy/docker/docker-compose.prod.yml up -d

# Check status
docker-compose -f deploy/docker/docker-compose.prod.yml ps

# View logs
docker-compose -f deploy/docker/docker-compose.prod.yml logs -f orchestrator
```

### 3. Verify Deployment

```bash
# Check API health
curl http://localhost:8000/health

# Check frontend
curl http://localhost:3000

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'
```

## Production Deployment (Kubernetes)

### 1. Create Namespace

```bash
kubectl apply -f deploy/k8s/namespace.yaml
```

### 2. Configure Secrets

```bash
# Create secrets from .env
kubectl create secret generic honeypot-secrets \
  --from-env-file=.env \
  -n adaptive-honeypot
```

Or edit the secrets template:
```bash
kubectl apply -f deploy/k8s/secrets.yaml
```

### 3. Deploy Infrastructure

```bash
# PostgreSQL
kubectl apply -f deploy/k8s/postgres.yaml

# Wait for PostgreSQL to be ready
kubectl wait --for=condition=ready pod -l app=postgresql -n adaptive-honeypot --timeout=300s

# Redis
kubectl apply -f deploy/k8s/redis.yaml

# Wait for Redis
kubectl wait --for=condition=ready pod -l app=redis -n adaptive-honeypot --timeout=120s
```

### 4. Deploy Application

```bash
# Backend
kubectl apply -f deploy/k8s/backend.yaml

# Frontend
kubectl apply -f deploy/k8s/frontend.yaml

# Ingress
kubectl apply -f deploy/k8s/ingress.yaml
```

### 5. Deploy Monitoring (Optional)

```bash
# Prometheus
kubectl apply -f deploy/k8s/prometheus.yaml

# Grafana
kubectl apply -f deploy/k8s/grafana.yaml
```

### 6. Verify Deployment

```bash
# Check pods
kubectl get pods -n adaptive-honeypot

# Check services
kubectl get svc -n adaptive-honeypot

# Check ingress
kubectl get ingress -n adaptive-honeypot

# Port forward for local access
kubectl port-forward svc/backend 8000:8000 -n adaptive-honeypot
kubectl port-forward svc/frontend 3000:80 -n adaptive-honeypot
```

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `AI_PROVIDER` | AI provider | Yes | openai |
| `AI_MODEL` | Model name | No | gpt-4-turbo-preview |
| `OPENAI_API_KEY` | OpenAI API key | Yes* | - |
| `ANTHROPIC_API_KEY` | Anthropic API key | Yes* | - |
| `GEMINI_API_KEY` | Gemini API key | Yes* | - |
| `DB_HOST` | PostgreSQL host | Yes | postgresql |
| `DB_PASSWORD` | Database password | Yes | - |
| `REDIS_HOST` | Redis host | Yes | redis |
| `SECURITY_JWT_SECRET` | JWT signing secret | Yes | - |

*At least one AI provider key is required

### Resource Limits

Default resource allocation:

```yaml
# Backend
requests:
  cpu: 250m
  memory: 512Mi
limits:
  cpu: 1000m
  memory: 1Gi

# Frontend
requests:
  cpu: 100m
  memory: 128Mi
limits:
  cpu: 500m
  memory: 256Mi

# PostgreSQL
requests:
  cpu: 250m
  memory: 512Mi
limits:
  cpu: 1000m
  memory: 2Gi
```

## Scaling

### Horizontal Scaling

```bash
# Scale backend
kubectl scale deployment backend --replicas=5 -n adaptive-honeypot

# Or rely on HPA
kubectl get hpa -n adaptive-honeypot
```

### Vertical Scaling

Edit resource limits in deployment files:
```yaml
resources:
  requests:
    cpu: 500m
    memory: 1Gi
  limits:
    cpu: 2000m
    memory: 2Gi
```

## Monitoring

### Prometheus Metrics

Access Prometheus UI:
```bash
kubectl port-forward svc/prometheus 9090:9090 -n adaptive-honeypot
```

Available at http://localhost:9090

### Grafana Dashboards

Access Grafana:
```bash
kubectl port-forward svc/grafana 3001:80 -n adaptive-honeypot
```

Default credentials: admin/admin

Pre-configured dashboards:
- Honeypot Overview
- Attack Metrics
- System Resources

## Upgrading

### Docker Compose

```bash
# Pull latest images
docker-compose -f deploy/docker/docker-compose.prod.yml pull

# Restart services
docker-compose -f deploy/docker/docker-compose.prod.yml up -d
```

### Kubernetes

```bash
# Update image
kubectl set image deployment/backend backend=honeypot/backend:v2.0.0 -n adaptive-honeypot

# Monitor rollout
kubectl rollout status deployment/backend -n adaptive-honeypot

# Rollback if needed
kubectl rollout undo deployment/backend -n adaptive-honeypot
```

## Backup and Recovery

### Database Backup

```bash
# PostgreSQL backup
kubectl exec -it postgresql-0 -n adaptive-honeypot -- \
  pg_dump -U honeypot adaptive_honeypot > backup.sql

# Restore
kubectl exec -it postgresql-0 -n adaptive-honeypot -- \
  psql -U honeypot adaptive_honeypot < backup.sql
```

### Volume Backup

```bash
# Snapshot PVC
kubectl get pvc -n adaptive-honeypot
```

## Troubleshooting

### Common Issues

1. **Pod not starting**
```bash
kubectl describe pod <pod-name> -n adaptive-honeypot
kubectl logs <pod-name> -n adaptive-honeypot
```

2. **Database connection errors**
```bash
# Check PostgreSQL
kubectl logs postgresql-0 -n adaptive-honeypot

# Verify secrets
kubectl get secrets -n adaptive-honeypot
```

3. **Honeypot containers not deploying**
```bash
# Check Docker socket mount
kubectl exec -it <backend-pod> -n adaptive-honeypot -- ls -la /var/run/docker.sock
```

### Log Collection

```bash
# Collect all logs
kubectl logs -l app=backend -n adaptive-honeypot --all-containers > backend.log
kubectl logs -l app=frontend -n adaptive-honeypot --all-containers > frontend.log
```