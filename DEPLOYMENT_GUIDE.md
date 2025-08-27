# 🚀 Aslan Drive Independent Deployment Guide

## Overview
Deploy Aslan Drive services independently for production environments using Portainer, systemd, or N8n scheduling. Each service runs autonomously with proper orchestration and monitoring.

## 🏗️ Architecture for Independent Deployment

### Always-Running Services
- **PostgreSQL**: Core database (24/7 uptime)
- **MD Provider API**: REST API for data access (24/7 uptime)

### Scheduled Services  
- **Data Ingestion**: Daily at 6:00 AM (scheduled execution)
- **Health Check**: Daily at 8:00 AM (scheduled execution)

### Weekly Maintenance
- **Database Backup**: Weekly automated backup
- **Host Restart**: Weekly system maintenance window

## 📋 Deployment Options

### Option 1: Portainer + Manual Scheduling (Recommended)
**Best for**: Production environments with Portainer UI management
- Visual container management
- Manual job triggering
- Resource monitoring and logs
- Easy scaling and updates

**Setup Steps**:
1. Deploy infrastructure stack (always running)
2. Deploy job containers (manual execution)
3. Set up external scheduling (systemd/cron)

### Option 2: Systemd Timers
**Best for**: Linux servers with systemd
- Native Linux scheduling
- Automatic startup and restart
- System journal logging
- Resource limits and security

### Option 3: N8n Workflows
**Best for**: Complex automation and monitoring
- Visual workflow editor
- Advanced error handling
- Integration with external systems
- Real-time monitoring and alerts

## 🛠️ Quick Start Deployment

### Step 1: Prepare Environment
```bash
# Clone repository
git clone <repository-url> /opt/aslan-drive
cd /opt/aslan-drive

# Build images
make docker-build

# Configure environment
cp .env.production .env
vim .env  # Edit passwords and URLs
```

### Step 2: Deploy Infrastructure (Always Running)
```bash
# Using Portainer
# 1. Import portainer/infrastructure-stack.yml
# 2. Set environment variables
# 3. Deploy stack

# OR using Docker Compose
docker-compose -f docker-compose.infrastructure.yml up -d
```

### Step 3: Set Up Scheduling

#### Option A: Systemd (Linux)
```bash
# Copy systemd files
sudo cp systemd/*.service /etc/systemd/system/
sudo cp systemd/*.timer /etc/systemd/system/

# Configure environment in service files
sudo vim /etc/systemd/system/aslan-data-ingestion.service

# Enable and start timers
sudo systemctl enable aslan-data-ingestion.timer
sudo systemctl enable aslan-health-check.timer
sudo systemctl start aslan-data-ingestion.timer
sudo systemctl start aslan-health-check.timer

# Verify
sudo systemctl list-timers aslan-*
```

#### Option B: Cron Jobs
```bash
# Add to root crontab
sudo crontab -e

# Add these lines:
0 6 * * * /opt/aslan-drive/scripts/run_data_ingestion.sh
0 8 * * * /opt/aslan-drive/scripts/run_health_check.sh
0 2 * * 0 /opt/aslan-drive/scripts/backup_database.sh
```

#### Option C: N8n Integration
```bash
# Import workflow
# 1. Load n8n/aslan-drive-workflow.json into N8n
# 2. Configure Portainer API credentials
# 3. Set up Slack webhook
# 4. Activate workflow
```

## 🔧 Service Configuration

### PostgreSQL Database
- **Restart Policy**: `unless-stopped`
- **Port**: 5432 (configurable)
- **Memory Limit**: 512MB
- **Backup**: Weekly automated
- **Health Check**: Built-in pg_isready

**Maintenance**:
```bash
# Weekly backup
docker exec aslan_postgres pg_dump -U trader aslan_drive > backup_$(date +%Y%m%d).sql

# Manual restart (maintenance window)
docker restart aslan_postgres

# Check logs
docker logs aslan_postgres
```

### MD Provider API
- **Restart Policy**: `unless-stopped`  
- **Port**: 8000 (configurable)
- **Memory Limit**: 256MB
- **Health Endpoint**: `/health`
- **Auto-scaling**: Load balancer ready

**Monitoring**:
```bash
# Health check
curl http://localhost:8000/health

# API documentation
curl http://localhost:8000/docs

# Resource usage
docker stats aslan_md_provider
```

### Data Ingestion Job
- **Execution**: Scheduled (not continuous)
- **Schedule**: Daily at 6:00 AM
- **Memory Limit**: 256MB
- **Timeout**: 30 minutes
- **Restart Policy**: No restart (job completion)

**Manual Execution**:
```bash
# Via script
./scripts/run_data_ingestion.sh

# Via Portainer
# Start container: aslan_data_ingestion_manual

# Via N8n
# Trigger workflow manually
```

### Health Check Job
- **Execution**: Scheduled (not continuous)
- **Schedule**: Daily at 8:00 AM (after data ingestion)
- **Memory Limit**: 128MB
- **Timeout**: 5 minutes
- **Notifications**: Slack integration

**Manual Execution**:
```bash
# Via script
./scripts/run_health_check.sh

# Check logs
tail -f /var/log/aslan/health_check_$(date +%Y%m%d).log
```

## 📊 Monitoring & Alerting

### Health Monitoring
- **Database**: Connection and data freshness checks
- **API**: Health endpoint and response times  
- **Jobs**: Execution status and completion
- **System**: Resource usage and logs

### Slack Integration
Configure webhook URL in environment:
```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

**Alert Types**:
- ✅ Daily health check success
- ❌ Data ingestion failures
- ⚠️ Database connectivity issues
- 📊 Weekly summary reports

### Log Management
**Locations**:
- Container logs: `docker logs <container>`
- Script logs: `/var/log/aslan/`
- System logs: `journalctl -u aslan-*`

**Retention**:
- Container logs: 7 days (Docker daemon config)
- Script logs: 30 days (automatic cleanup)
- System logs: 90 days (journalctl config)

## 🔒 Security & Backup

### Security Best Practices
- Use strong database passwords
- Limit network access to necessary ports
- Regular security updates
- Monitor access logs
- Encrypt backups

### Backup Strategy
- **Database**: Daily automated dumps
- **Configuration**: Version controlled
- **Logs**: Retained per policy
- **Container Images**: Tagged and stored

**Backup Script**:
```bash
#!/bin/bash
# Weekly backup script
DATE=$(date +%Y%m%d)
docker exec aslan_postgres pg_dump -U trader aslan_drive | gzip > /backup/aslan_${DATE}.sql.gz

# Cleanup old backups (keep 12 weeks)
find /backup -name "aslan_*.sql.gz" -mtime +84 -delete
```

## 🚦 Troubleshooting

### Common Issues

#### Data Ingestion Fails
```bash
# Check database connectivity
docker exec aslan_postgres pg_isready -U trader

# Check network
docker network inspect aslan_network

# Review logs
tail -f /var/log/aslan/data_ingestion_$(date +%Y%m%d).log
```

#### Health Check Fails
```bash
# Manual health check
curl http://localhost:8000/health

# Check Slack webhook
curl -X POST $SLACK_WEBHOOK_URL -d '{"text":"Test message"}'

# Check data freshness
docker exec aslan_postgres psql -U trader -d aslan_drive -c "SELECT MAX(date) FROM daily_ohlcv;"
```

#### Service Won't Start
```bash
# Check dependencies
docker ps | grep aslan

# Check resources
df -h
free -m

# Check systemd status
sudo systemctl status aslan-data-ingestion.timer
sudo journalctl -u aslan-data-ingestion.service
```

### Performance Tuning

#### Database Optimization
```sql
-- PostgreSQL tuning for time-series data
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
SELECT pg_reload_conf();
```

#### Container Resource Limits
```yaml
# Adjust in docker-compose files
deploy:
  resources:
    limits:
      memory: 512M
      cpus: '0.5'
    reservations:
      memory: 256M
      cpus: '0.25'
```

## 🔄 Maintenance Windows

### Weekly Maintenance (Sunday 2:00 AM)
1. **Stop Scheduled Jobs**: Disable timers/workflows
2. **Backup Database**: Full backup and verification
3. **Update Images**: Pull latest versions
4. **System Updates**: OS and security patches
5. **Restart Services**: Clean restart of all services
6. **Verify Health**: Run health checks
7. **Re-enable Scheduling**: Activate timers/workflows

### Monthly Maintenance
- Review and archive logs
- Update SSL certificates
- Security audit
- Performance review
- Capacity planning

## 📈 Scaling Considerations

### Horizontal Scaling
- **MD Provider**: Multiple instances behind load balancer
- **Database**: Read replicas for API queries
- **Jobs**: Parallel execution with data partitioning

### Vertical Scaling
- **Memory**: Increase container limits based on data volume
- **CPU**: Scale up for faster processing
- **Storage**: Monitor database growth and extend volumes

### High Availability
- **Database**: Master-slave replication
- **API**: Multiple instances with health checks
- **Scheduling**: Redundant scheduling systems
- **Monitoring**: Multiple alert channels