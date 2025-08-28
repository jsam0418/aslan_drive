# Local CI/CD Testing Guide

This guide explains how to run the entire CI/CD pipeline locally to ensure your changes pass before pushing to GitHub.

## Quick Start

```bash
# Option 1: Simple make command
make ci-local

# Option 2: Comprehensive shell script
./scripts/ci-local.sh

# Option 3: Individual components
make build
make format-check
make lint
make typecheck
```

## Testing Options

### 1. Make Command Approach

The simplest way to test locally:

```bash
make ci-local
```

This runs:
- Schema generation (`make build`)
- Code formatting check (`make format-check`) 
- Import sorting check (`make lint`)
- Type checking (`make typecheck`)

### 2. Comprehensive Shell Script

For detailed testing with colored output:

```bash
./scripts/ci-local.sh
```

This comprehensive script includes:
- ✅ Prerequisites checking (Python, Docker, tools)
- 🔧 Schema generation testing
- 🎨 Code formatting validation (black)
- 📦 Import sorting validation (isort)
- 🔍 Type checking validation (mypy)
- 🧪 Basic functionality tests
- 🐳 Docker build simulation
- 🔗 Integration test simulation
- 🛡️ Basic security checks
- 📊 Detailed reporting with colored output

### 3. Individual Component Testing

Test specific components individually:

```bash
# Schema generation
make schema-gen
python3 tools/schema_generator.py

# Code formatting
make format          # Apply formatting
make format-check    # Check formatting only

# Import sorting
make lint            # Check import sorting

# Type checking
make typecheck       # Run mypy

# Basic tests
python3 test_basic.py
make test           # If dependencies installed
```

### 4. GitHub Actions Local Runner (Advanced)

For exact GitHub Actions simulation:

```bash
# Install act (GitHub Actions local runner)
# macOS:
brew install act

# Linux:
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run specific workflow
act -j format-check
act -j type-check
act -j build-and-test

# Run all jobs
act
```

## Prerequisites

### Required Tools

```bash
# Python 3.11+
python3 --version

# Docker
docker --version

# Development dependencies (optional but recommended)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Tool Installation

If tools are missing, install them:

```bash
# Install formatting tools
pip install black isort mypy

# Or install all dev dependencies
pip install -r requirements.txt
```

## Common Issues and Solutions

### Formatting Issues

```bash
# Fix formatting issues
make format

# Check what would be changed
black --check --diff .
```

### Import Sorting Issues

```bash
# Fix import sorting
isort .

# Check what would be changed  
isort --check-only --diff .
```

### Type Checking Issues

```bash
# Run type checking with detailed output
mypy --show-error-codes --pretty .

# Check specific file
mypy services/data_ingestion/main.py
```

### Docker Issues

```bash
# Test Docker builds individually
docker build -f services/data_ingestion/Dockerfile -t test-data-ingestion .
docker build -f services/health_check/Dockerfile -t test-health-check .
docker build -f services/md_provider/Dockerfile -t test-md-provider .
```

## Integration with Development Workflow

### Pre-commit Hook (Recommended)

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
echo "Running local CI/CD checks..."
make ci-local
if [ $? -ne 0 ]; then
    echo "❌ CI/CD checks failed. Please fix issues before committing."
    exit 1
fi
echo "✅ All checks passed!"
```

```bash
chmod +x .git/hooks/pre-commit
```

### Development Cycle

1. Make your changes
2. Run `make ci-local` or `./scripts/ci-local.sh`
3. Fix any issues found
4. Commit and push
5. GitHub Actions will pass ✅

### VS Code Integration

Add to `.vscode/tasks.json`:

```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Local CI/CD",
            "type": "shell",
            "command": "make",
            "args": ["ci-local"],
            "group": "test",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            },
            "problemMatcher": []
        }
    ]
}
```

Then use `Ctrl+Shift+P` → "Tasks: Run Task" → "Local CI/CD"

## Troubleshooting

### Permission Issues

```bash
# Make scripts executable
chmod +x scripts/ci-local.sh
chmod +x scripts/setup-act.sh
```

### Virtual Environment Issues

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Docker Issues

```bash
# Check Docker is running
docker info

# Clean up Docker resources
docker system prune -f
```

## Performance Tips

- Use `make ci-local` for quick checks
- Use `./scripts/ci-local.sh` for comprehensive testing
- Run individual commands during active development
- Use pre-commit hooks to catch issues early
- Cache virtual environments and Docker layers

## Output Examples

### Successful Run

```
✅ Prerequisites Check: All required tools found
🔧 Schema Generation: SUCCESS
🎨 Code Formatting: SUCCESS  
📦 Import Sorting: SUCCESS
🔍 Type Checking: SUCCESS
🧪 Basic Tests: SUCCESS
🐳 Docker Builds: SUCCESS
🔗 Integration Tests: SUCCESS  
🛡️ Security Checks: SUCCESS

🎉 All local CI/CD checks passed! Ready to push.
```

### Failed Run

```
❌ Code Formatting: FAILED
   - services/data_ingestion/main.py needs formatting
   - Run: black services/data_ingestion/main.py

❌ Type Checking: FAILED  
   - services/md_provider/api.py:45: error: Missing return type

🛑 Fix the above issues before pushing.
```

This comprehensive testing approach ensures your code will pass GitHub Actions before you push, saving time and maintaining code quality.