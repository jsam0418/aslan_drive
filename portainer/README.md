# Portainer Deployment Guide

This directory contains Portainer stack configurations for deploying Aslan Drive services.

## Stack Architecture

### Infrastructure Stack (Always Running)
- **PostgreSQL**: Database service (24/7)
- **MD Provider API**: REST API for market data (24/7)

### Scheduled Jobs Stack (Manual Execution)
- **Data Ingestion**: Manual job execution container
- **Health Check**: Manual job execution container

## Deployment Steps

### 1. Deploy Infrastructure Stack

1. In Portainer, go to **Stacks** → **Add stack**
2. Name: `aslan-infrastructure`
3. Upload `infrastructure-stack.yml`
4. Set environment variables:
   ```
   POSTGRES_PASSWORD=your_secure_password
   DOCKER_REGISTRY=ghcr.io/your-username/aslan-drive
   IMAGE_TAG=latest
   ```
5. Deploy the stack

### 2. Deploy Scheduled Jobs Stack

1. In Portainer, go to **Stacks** → **Add stack**  
2. Name: `aslan-scheduled-jobs`
3. Upload `k8s-cronjobs-stack.yml`
4. Set environment variables (same as above)
5. Deploy the stack

### 3. Manual Job Execution

To run jobs manually in Portainer:

1. Go to **Containers**
2. Find the job container (e.g., `aslan_data_ingestion_manual`)
3. Click **Start** to execute the job
4. Monitor logs in real-time
5. Container will stop automatically when job completes

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Required
POSTGRES_PASSWORD=your_secure_password
DOCKER_REGISTRY=ghcr.io/your-username/aslan-drive

# Optional
IMAGE_TAG=latest
LOG_LEVEL=info
SLACK_WEBHOOK_URL=https://hooks.slack.com/your/webhook/url
```

## Scheduling with External Cron

For automated scheduling, use host cron with Portainer API:

```bash
# Daily data ingestion at 6:00 AM
0 6 * * * curl -X POST "http://localhost:9000/api/endpoints/1/docker/containers/aslan_data_ingestion_manual/start" -H "Authorization: Bearer YOUR_API_KEY"

# Daily health check at 8:00 AM  
0 8 * * * curl -X POST "http://localhost:9000/api/endpoints/1/docker/containers/aslan_health_check_manual/start" -H "Authorization: Bearer YOUR_API_KEY"
```

## Monitoring

- **Container Logs**: Available in Portainer UI
- **Resource Usage**: Monitor CPU/Memory in container stats
- **Health Checks**: MD Provider has built-in health endpoint
- **Job Status**: Check container exit codes for job success/failure

## Upgrading

To upgrade to newer image versions:

1. Update `IMAGE_TAG` in stack environment variables
2. Redeploy the stack
3. Portainer will pull the latest image automatically

## Transition to Kubernetes

When ready to move to Kubernetes:

1. Apply the K8s manifests from `k8s/` directory
2. Remove the Portainer scheduled jobs stack
3. Keep the infrastructure stack if needed for development