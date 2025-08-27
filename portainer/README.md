# Portainer Deployment Guide

## Overview
Deploy Aslan Drive services independently using Portainer stacks for maximum flexibility and control.

## Prerequisites
- Portainer CE/EE running on Docker
- Docker images built and available in registry
- Environment variables configured

## Deployment Order

### 1. Infrastructure Stack (Deploy First)
**Stack Name**: `aslan-infrastructure`
**File**: `infrastructure-stack.yml`
**Services**: PostgreSQL + MD Provider API
**Restart Policy**: Always running

**Environment Variables**:
```bash
POSTGRES_PASSWORD=your_secure_password
POSTGRES_PORT=5432
MD_PROVIDER_PORT=8000
LOG_LEVEL=info
API_DOMAIN=api.aslan-drive.local
IMAGE_TAG=latest
```

**Pre-deployment Steps**:
1. Upload `generated/migration.sql` to Portainer file manager at `/data/migration.sql`
2. Ensure images are available: `aslan_drive_md_provider:latest`

### 2. Scheduled Jobs Stack (Optional for Testing)
**Stack Name**: `aslan-scheduled-jobs`
**File**: `scheduled-jobs-stack.yml`
**Services**: Data ingestion + Health check jobs
**Restart Policy**: Manual execution only

**Environment Variables**:
```bash
POSTGRES_PASSWORD=your_secure_password
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK
LOG_LEVEL=info
IMAGE_TAG=latest
```

## Manual Job Execution via Portainer

### Running Data Ingestion
1. Go to **Containers** page
2. Find `aslan_data_ingestion_manual` 
3. Click **Start** to run one-time ingestion
4. Monitor logs in **Logs** tab
5. Container will stop automatically when complete

### Running Health Check
1. Go to **Containers** page
2. Find `aslan_health_check_manual`
3. Click **Start** to run health verification
4. Check logs for results and Slack notifications
5. Container will stop automatically when complete

## External Scheduling Options

### Option 1: Systemd Timers (Recommended)
Use systemd service files in `/systemd/` directory:
```bash
# Copy services to systemd
sudo cp systemd/*.service /etc/systemd/system/
sudo cp systemd/*.timer /etc/systemd/system/

# Configure environment variables
sudo vim /etc/systemd/system/aslan-data-ingestion.service

# Enable and start timers
sudo systemctl enable aslan-data-ingestion.timer
sudo systemctl enable aslan-health-check.timer
sudo systemctl start aslan-data-ingestion.timer
sudo systemctl start aslan-health-check.timer

# Check status
sudo systemctl status aslan-data-ingestion.timer
sudo systemctl list-timers aslan-*
```

### Option 2: Cron Jobs
```bash
# Add to crontab
0 6 * * * /opt/aslan-drive/scripts/run_data_ingestion.sh
0 8 * * * /opt/aslan-drive/scripts/run_health_check.sh
```

### Option 3: N8n Workflows
- Create workflow nodes to trigger Docker containers
- Use HTTP requests to Portainer API
- Set up error handling and notifications

## Monitoring & Maintenance

### Database Backups
```bash
# Weekly backup script (add to cron)
docker exec aslan_postgres pg_dump -U trader aslan_drive > backup_$(date +%Y%m%d).sql
```

### Log Management
Logs are stored in:
- Container logs: Portainer UI or `docker logs`
- Script logs: `/var/log/aslan/`
- System logs: `journalctl -u aslan-*`

### Health Monitoring
- API health endpoint: `http://localhost:8000/health`
- Database connectivity: Built into health check service
- Slack notifications: Configure webhook URL

## Scaling Considerations

### Resource Limits
- PostgreSQL: 512MB memory limit
- MD Provider: 256MB memory limit  
- Jobs: 256MB memory limit each

### Performance Tuning
- Adjust `shared_buffers` in PostgreSQL config
- Scale MD Provider horizontally behind load balancer
- Monitor job execution times and adjust schedules

### High Availability
- Use external PostgreSQL cluster
- Deploy MD Provider on multiple nodes
- Implement backup/restore procedures