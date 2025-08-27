# 🚀 CI/CD Guide for Aslan Drive

## Overview
Comprehensive CI/CD pipeline using GitHub Actions for automated testing, building, security scanning, and deployment of the Aslan Drive trading infrastructure.

## 📋 Workflow Overview

### 1. Main CI/CD Pipeline (`ci.yml`)
**Triggers**: Push/PR to main/master/develop branches, manual dispatch
**Jobs**:
- **Code Quality & Testing**: Formatting, linting, type checking, unit tests
- **Docker Build**: Multi-service container building and testing
- **Security Scanning**: Bandit, Safety, dependency scanning
- **Integration Tests**: Full database integration testing
- **Performance Tests**: Load testing (main branch only)

### 2. Release Pipeline (`release.yml`) 
**Triggers**: Git tags (v*), manual dispatch
**Jobs**:
- **Build & Publish**: Multi-arch Docker images to GitHub Container Registry
- **Create Release**: Automated GitHub releases with changelogs
- **Deployment Issues**: Auto-generated deployment checklists
- **Notifications**: Slack alerts for successful releases

### 3. Security Pipeline (`security.yml`)
**Triggers**: Weekly schedule, push/PR to main, manual dispatch
**Jobs**:
- **Container Security**: Trivy vulnerability scanning
- **Code Security**: Bandit, Semgrep, CodeQL analysis
- **Dependency Scanning**: Safety, pip-audit, GitHub dependency review
- **Secrets Scanning**: TruffleHog, GitLeaks
- **SAST Analysis**: Static application security testing

### 4. Performance Pipeline (`performance.yml`)
**Triggers**: Weekly schedule, changes to services, manual dispatch
**Jobs**:
- **API Performance**: Locust load testing with concurrent users
- **Database Performance**: Bulk operations and query performance
- **Resource Usage**: Memory profiling and resource monitoring

## 🔧 Setup Instructions

### 1. Repository Secrets
Configure these secrets in GitHub repository settings:

#### Required Secrets
```bash
# For container registry (automatically available)
GITHUB_TOKEN  # Automatically provided by GitHub

# For Slack notifications (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# For code coverage (optional)
CODECOV_TOKEN=your_codecov_token
```

#### Optional Secrets for Enhanced Features
```bash
# For additional security scanning
SNYK_TOKEN=your_snyk_token

# For custom registry (if not using GitHub Container Registry)
DOCKER_REGISTRY_USERNAME=your_username
DOCKER_REGISTRY_PASSWORD=your_password
```

### 2. Repository Settings

#### Branch Protection Rules
Configure protection for `main`/`master` branch:
- ✅ Require pull request reviews before merging
- ✅ Require status checks to pass before merging
  - `test-and-quality`
  - `docker-build`
  - `security-scan`
  - `integration-test`
- ✅ Require branches to be up to date before merging
- ✅ Restrict pushes that create files over 100 MB

#### Code Scanning
- ✅ Enable CodeQL analysis (automatically configured)
- ✅ Enable Dependabot alerts
- ✅ Enable secret scanning

### 3. Container Registry Setup

#### GitHub Container Registry (Recommended)
```bash
# Registry: ghcr.io
# Images will be published as:
# ghcr.io/your-username/aslan-drive_base:latest
# ghcr.io/your-username/aslan-drive_data_ingestion:latest
# ghcr.io/your-username/aslan-drive_md_provider:latest
# ghcr.io/your-username/aslan-drive_health_check:latest
```

#### Custom Registry Setup
If using a custom registry, update environment variables in workflows:
```yaml
env:
  REGISTRY: your-registry.com
  IMAGE_NAME: your-namespace/aslan-drive
```

## 🏃‍♂️ Running Workflows

### Automatic Triggers
- **Push to main/master**: Full CI pipeline + security scan
- **Pull Requests**: Full CI pipeline excluding performance tests
- **Tag push (v\*)**: Release pipeline with image publishing
- **Weekly (Sunday 2 AM)**: Security scanning
- **Weekly (Saturday 3 AM)**: Performance testing

### Manual Triggers
```bash
# Trigger CI pipeline manually
gh workflow run ci.yml

# Trigger release with custom tag
gh workflow run release.yml -f tag=v0.2.0

# Run security scan
gh workflow run security.yml

# Run performance tests with custom parameters
gh workflow run performance.yml -f duration=120 -f users=20
```

## 📊 Monitoring & Reports

### GitHub Actions Dashboard
Monitor workflow status at: `https://github.com/your-repo/actions`

### Artifacts and Reports
Each workflow produces downloadable artifacts:
- **CI Pipeline**: Test coverage reports, build logs
- **Security Pipeline**: Vulnerability reports (SARIF, JSON, TXT)
- **Performance Pipeline**: Load test reports, memory usage
- **Release Pipeline**: Deployment checklists, changelogs

### Status Badges
Add to your README.md:
```markdown
[![CI/CD](https://github.com/your-username/aslan-drive/workflows/CI%2FCD%20Pipeline/badge.svg)](https://github.com/your-username/aslan-drive/actions)
[![Security](https://github.com/your-username/aslan-drive/workflows/Security%20Scanning/badge.svg)](https://github.com/your-username/aslan-drive/actions)
[![Release](https://github.com/your-username/aslan-drive/workflows/Release%20and%20Deploy/badge.svg)](https://github.com/your-username/aslan-drive/releases)
```

## 🔨 Development Workflow

### 1. Feature Development
```bash
# Create feature branch
git checkout -b feature/new-endpoint

# Make changes, run local tests
make build
make test
python test_basic.py

# Commit and push
git add .
git commit -m "Add new endpoint for symbol filtering"
git push origin feature/new-endpoint

# Create PR (triggers CI pipeline)
gh pr create --title "Add symbol filtering endpoint" --body "..."
```

### 2. Code Quality Checks
Before pushing, run local checks:
```bash
# Format code
make format

# Check linting
make lint

# Run type checking
make typecheck

# Run tests
make test

# Build Docker images
make docker-build
```

### 3. Release Process
```bash
# Update version and create tag
git tag -a v0.2.0 -m "Release version 0.2.0"
git push origin v0.2.0

# Release pipeline automatically:
# 1. Builds and publishes Docker images
# 2. Creates GitHub release
# 3. Generates deployment checklist
# 4. Sends Slack notification
```

## 🚨 Troubleshooting

### Common CI/CD Issues

#### 1. Build Failures
```bash
# Check workflow logs
gh run list --workflow=ci.yml
gh run view RUN_ID --log

# Common fixes:
# - Update dependencies in requirements.txt
# - Fix code formatting: make format
# - Resolve merge conflicts
# - Check Docker base image updates
```

#### 2. Test Failures
```bash
# Run tests locally to debug
make build
make test
python test_basic.py

# Check test isolation issues
python -m pytest tests/ -v --tb=long
```

#### 3. Security Scan Failures
```bash
# Review security reports in workflow artifacts
# Common issues:
# - Update vulnerable dependencies
# - Fix code security issues found by Bandit
# - Rotate exposed secrets
```

#### 4. Performance Degradation
```bash
# Review performance reports
# Check for:
# - Database query optimization needs
# - Memory leaks in data generation
# - API response time increases
```

### Workflow Debugging
```bash
# Enable debug logging
gh workflow run ci.yml --ref main
# Add this to workflow: ACTIONS_STEP_DEBUG: true

# Download workflow logs
gh run download RUN_ID

# Check specific job logs
gh api repos/:owner/:repo/actions/runs/RUN_ID/jobs
```

## ⚡ Optimization Tips

### 1. Faster Builds
- ✅ Docker layer caching enabled (GitHub Actions Cache)
- ✅ Python dependency caching
- ✅ Multi-stage Docker builds
- ✅ Parallel job execution

### 2. Efficient Testing
- ✅ Separate unit and integration tests
- ✅ Database fixtures and cleanup
- ✅ Conditional performance tests
- ✅ Test result caching

### 3. Security Best Practices
- ✅ Least privilege GitHub tokens
- ✅ Secret scanning enabled
- ✅ Dependency vulnerability monitoring
- ✅ Container image scanning

### 4. Cost Optimization
- ✅ Conditional workflow execution
- ✅ Artifact retention policies
- ✅ Efficient resource usage
- ✅ Scheduled vs. trigger-based scanning

## 📈 Metrics and Analytics

### Key Metrics to Monitor
- **Build Success Rate**: % of successful CI runs
- **Build Time**: Average pipeline execution time
- **Test Coverage**: Code coverage percentage
- **Security Score**: Number of vulnerabilities found
- **Performance Trends**: Response time and resource usage over time

### Integration with Monitoring Tools
```bash
# Example: Send metrics to external monitoring
# Add to workflow:
- name: Send metrics
  run: |
    curl -X POST "https://your-monitoring-service.com/metrics" \
      -d "build_time=${{ env.BUILD_TIME }}" \
      -d "test_coverage=${{ env.COVERAGE }}"
```

## 🔄 Maintenance

### Weekly Tasks
- Review security scan reports
- Update dependencies via Dependabot PRs
- Monitor performance trends
- Check workflow success rates

### Monthly Tasks
- Review and update workflow configurations
- Audit repository permissions
- Update documentation
- Clean up old workflow runs and artifacts

### Quarterly Tasks
- Security audit of CI/CD pipeline
- Performance benchmarking
- Update GitHub Actions versions
- Review and update branch protection rules