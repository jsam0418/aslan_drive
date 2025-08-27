# N8n Workflow Integration

## Overview
Automate Aslan Drive data pipeline using N8n workflows with Docker container orchestration via Portainer API.

## Workflow Features
- **Daily Scheduling**: Runs data ingestion at 6:00 AM daily
- **Error Handling**: Automatic failure detection and Slack alerts
- **Sequential Execution**: Data ingestion → Health check
- **Container Management**: Automatic cleanup after execution
- **Monitoring**: Real-time status tracking and notifications

## Prerequisites

### N8n Setup
1. N8n instance running (Docker/Cloud)
2. Access to Portainer API
3. Network connectivity to Docker host

### Required Credentials in N8n

#### 1. Portainer API Token
- **Credential Type**: HTTP Header Auth
- **Name**: `Portainer API Token` 
- **Header Name**: `X-API-Key`
- **Header Value**: Your Portainer API token

To get Portainer API token:
```bash
# Login to Portainer and create API token
curl -X POST http://portainer.local:9000/api/auth \
  -H "Content-Type: application/json" \
  -d '{"Username":"admin","Password":"your_password"}'

# Use returned JWT token to create API key
curl -X POST http://portainer.local:9000/api/users/admin/tokens \
  -H "Authorization: Bearer JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"description":"Aslan Drive N8n Integration"}'
```

#### 2. Slack Webhook (Optional)
- **Credential Type**: Slack Webhook
- **Name**: `Slack Webhook`
- **Webhook URL**: Your Slack webhook URL

### Environment Variables in N8n
Set these in N8n environment or workflow settings:
```bash
POSTGRES_PASSWORD=your_database_password
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
PORTAINER_URL=http://portainer.local:9000
```

## Workflow Import

### 1. Import Workflow
1. Go to N8n UI → Workflows → Import
2. Upload `aslan-drive-workflow.json`
3. Configure credentials as described above

### 2. Customize Settings
Edit the workflow to match your environment:

- **Portainer URL**: Update all HTTP request URLs
- **Container Images**: Ensure image names match your registry
- **Network Name**: Verify `aslan_network` exists
- **Schedule**: Modify cron expression if needed

### 3. Test Workflow
1. Click **Execute Workflow** to test manually
2. Monitor execution in N8n logs
3. Verify containers are created/started in Portainer
4. Check Slack for notifications

## Workflow Logic

### 1. Daily Trigger (6:00 AM)
```javascript
// Cron expression: "0 6 * * *"
// Runs every day at 6:00 AM
```

### 2. Data Ingestion Phase
1. **Create Container**: Via Portainer API
2. **Start Container**: Execute data ingestion
3. **Wait**: 30 seconds for completion
4. **Check Status**: Verify exit code

### 3. Success Path
- Exit code = 0 → Continue to health check
- Wait 2 minutes for data settling
- Execute health check container
- Cleanup containers

### 4. Failure Path
- Exit code ≠ 0 → Send Slack alert
- Include error details and container info
- Cleanup containers

## Customization Options

### Modify Schedule
Edit the **Daily Trigger** node:
```javascript
// Examples:
"0 6 * * 1-5"     // Weekdays only at 6 AM
"0 */6 * * *"     // Every 6 hours
"0 6,18 * * *"    // 6 AM and 6 PM daily
```

### Add Retry Logic
Insert **If** node after status check:
```javascript
// Retry up to 3 times on failure
if (attempt < 3) {
  // Wait and retry
  return "retry";
} else {
  // Send failure alert
  return "failed";
}
```

### Multiple Environment Support
Use environment-specific workflows:
- `aslan-drive-production.json`
- `aslan-drive-staging.json`
- Different Portainer endpoints
- Separate Slack channels

### Advanced Monitoring
Add webhook nodes to send status updates:
- **Started**: Data ingestion beginning
- **Progress**: Mid-process status
- **Completed**: Success confirmation
- **Failed**: Detailed error information

## Troubleshooting

### Common Issues

#### 1. Portainer Connection Failed
```bash
# Check Portainer accessibility
curl -I http://portainer.local:9000/api/system/status

# Verify API token
curl -H "X-API-Key: YOUR_TOKEN" \
     http://portainer.local:9000/api/endpoints
```

#### 2. Container Creation Failed
- Verify image exists in registry
- Check network `aslan_network` exists
- Ensure Portainer has Docker access

#### 3. Workflow Execution Timeout
- Increase wait times in workflow
- Check container resource limits
- Monitor Docker host performance

#### 4. Slack Notifications Not Working
- Test webhook URL manually
- Verify N8n has internet access
- Check Slack app permissions

### Debug Tips
1. **Enable Debug Mode**: Set workflow to save execution data
2. **Manual Testing**: Run individual nodes manually
3. **Container Logs**: Check Portainer container logs
4. **N8n Logs**: Monitor N8n execution logs
5. **Network Connectivity**: Test all API endpoints

## Production Considerations

### Security
- Use encrypted credentials storage
- Rotate API tokens regularly
- Implement webhook authentication
- Network segmentation for N8n

### Reliability
- Set up N8n high availability
- Monitor workflow execution status  
- Implement alerting for workflow failures
- Regular backup of workflow configurations

### Performance
- Optimize container resource limits
- Use container registries close to execution
- Monitor workflow execution times
- Scale N8n workers for concurrent workflows