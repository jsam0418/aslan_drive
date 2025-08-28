# Aslan Drive - Kubernetes & Portainer Deployment Guide

Container-based deployment with Kubernetes CronJobs and Portainer integration for automated job scheduling and image management.

## Architecture Overview

### Container Strategy
- **Individual Containers**: Each service has its own container image
- **GitHub Container Registry**: All images built and stored in GHCR
- **Automated CI/CD**: Images automatically built on code changes
- **Kubernetes CronJobs**: Automated job scheduling
- **Portainer Integration**: Manual job execution and management

### Services
- **Data Ingestion**: Scheduled daily data processing (6 AM UTC)
- **Health Check**: Database validation with Slack notifications (8 AM UTC)
- **MD Provider API**: REST API for market data (always running)
- **PostgreSQL**: Database service (always running)

## Container Images

All images are built automatically via GitHub Actions and pushed to GitHub Container Registry:

```
ghcr.io/[USERNAME]/aslan-drive-data-ingestion:latest
ghcr.io/[USERNAME]/aslan-drive-health-check:latest
ghcr.io/[USERNAME]/aslan-drive-md-provider:latest
```

## Deployment Options

### Option 1: Kubernetes with CronJobs (Recommended)

#### Prerequisites
- Kubernetes cluster (K3s, K8s, etc.)
- kubectl configured
- Access to GitHub Container Registry

#### Quick Deploy
```bash
# 1. Clone repository
git clone <repository-url>
cd aslan_drive

# 2. Update image references in k8s/ manifests
# Edit k8s/cronjobs/*.yaml and k8s/deployments/*.yaml
# Replace [YOUR_GITHUB_USERNAME] with your actual username

# 3. Create namespace and secrets
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml

# 4. Deploy MD Provider (always running)
kubectl apply -f k8s/deployments/md-provider-deployment.yaml

# 5. Deploy CronJobs (scheduled execution)
kubectl apply -f k8s/cronjobs/data-ingestion-cronjob.yaml
kubectl apply -f k8s/cronjobs/health-check-cronjob.yaml
```

#### Verify Deployment
```bash
# Check CronJobs
kubectl get cronjobs -n aslan-drive

# Check deployments
kubectl get deployments -n aslan-drive

# View job execution history
kubectl get jobs -n aslan-drive

# Check logs
kubectl logs -n aslan-drive -l app=aslan-drive
```

### Option 2: Portainer Stacks

#### Deploy Infrastructure
1. Open Portainer UI
2. Go to **Stacks** → **Add stack**
3. Name: `aslan-infrastructure`
4. Upload `portainer/infrastructure-stack.yml`
5. Set environment variables:
   ```
   DOCKER_REGISTRY=ghcr.io/your-username/aslan-drive
   POSTGRES_PASSWORD=your_secure_password
   IMAGE_TAG=latest
   ```

#### Deploy Scheduled Jobs
1. Create stack: `aslan-scheduled-jobs`
2. Upload `portainer/k8s-cronjobs-stack.yml`
3. Use same environment variables

#### Manual Job Execution
- Go to **Containers** in Portainer
- Find job container (e.g., `aslan_data_ingestion_manual`)
- Click **Start** to run job
- Monitor logs in real-time

### Option 3: Local Development

```bash
# Generate schema
python3 tools/schema_generator.py

# Build all images
docker-compose --profile build up --build

# Start infrastructure
docker-compose up -d postgres md_provider

# Run jobs manually
docker run --rm --network aslan_drive_aslan_network \
  -e "DATABASE_URL=postgresql://trader:trading123@postgres:5432/aslan_drive" \
  aslan-drive-data-ingestion:latest

docker run --rm --network aslan_drive_aslan_network \
  -e "DATABASE_URL=postgresql://trader:trading123@postgres:5432/aslan_drive" \
  aslan-drive-health-check:latest
```

## Configuration

### Environment Variables

**Required:**
- `DATABASE_URL`: PostgreSQL connection string
- `POSTGRES_PASSWORD`: Database password

**Optional:**
- `SLACK_WEBHOOK_URL`: Slack notifications
- `LOG_LEVEL`: Logging level (info, debug, error)
- `IMAGE_TAG`: Container image tag

### Secrets Management

#### Kubernetes
```bash
# Create database secret
kubectl create secret generic aslan-drive-secrets \
  --from-literal=database-url="postgresql://user:pass@postgres:5432/aslan_drive" \
  --from-literal=slack-webhook-url="https://hooks.slack.com/your/webhook" \
  -n aslan-drive
```

#### Portainer
Set environment variables in stack configuration.

## CI/CD Pipeline

### GitHub Actions Workflow
1. **Code Quality**: Linting, type checking, tests
2. **Build Images**: Individual containers for each service
3. **Push to GHCR**: Automatic image publishing
4. **Integration Tests**: Full system testing

### Image Tags
- `latest`: Latest main branch
- `main-<sha>`: Specific commit
- `develop`: Development branch

### Upgrading Production
```bash
# Kubernetes: Update image tag and apply
kubectl set image cronjob/aslan-data-ingestion \
  data-ingestion=ghcr.io/username/aslan-drive-data-ingestion:new-tag \
  -n aslan-drive

# Portainer: Update IMAGE_TAG in stack environment variables
```

## Monitoring & Troubleshooting

### Job Status
```bash
# Kubernetes: Check CronJob status
kubectl describe cronjob aslan-data-ingestion -n aslan-drive

# View job logs
kubectl logs job/aslan-data-ingestion-<timestamp> -n aslan-drive

# Portainer: View container logs in UI
```

### Common Issues

**Image Pull Failures:**
- Verify GitHub Container Registry access
- Check image tag exists
- Ensure GHCR authentication

**Job Execution Failures:**
- Check database connectivity
- Verify environment variables
- Review container logs

**Resource Issues:**
- Monitor CPU/memory usage
- Adjust resource limits in manifests
- Check cluster resource availability

### Health Checks

**MD Provider API:**
```bash
curl http://localhost:8000/health
```

**Database:**
```bash
kubectl exec -it postgres-pod -n aslan-drive -- pg_isready -U trader
```

## File Structure
```
aslan_drive/
├── k8s/                          # Kubernetes manifests
│   ├── cronjobs/                 # CronJob definitions
│   ├── deployments/              # Service deployments  
│   ├── namespace.yaml            # Namespace definition
│   └── secrets.yaml              # Secret templates
├── portainer/                    # Portainer configurations
│   ├── infrastructure-stack.yml  # Always-running services
│   ├── k8s-cronjobs-stack.yml   # Manual job containers
│   └── README.md                 # Portainer guide
├── services/                     # Service code + Dockerfiles
│   ├── data_ingestion/
│   ├── health_check/
│   └── md_provider/
└── .github/workflows/ci.yml      # CI/CD pipeline
```

## Production Recommendations

1. **Security**: Use proper secrets management
2. **Monitoring**: Set up log aggregation (ELK, Grafana)
3. **Backup**: Regular database backups
4. **Scaling**: Configure resource limits appropriately
5. **Updates**: Automated image updates with proper testing