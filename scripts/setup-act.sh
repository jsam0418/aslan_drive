#!/bin/bash
# Setup script for Act - GitHub Actions local runner

set -e

echo "🎬 Setting up Act to run GitHub Actions locally..."

# Check if act is already installed
if command -v act &> /dev/null; then
    echo "✅ Act is already installed!"
    act --version
    exit 0
fi

# Detect architecture
ARCH=$(uname -m)
case $ARCH in
    x86_64)
        ARCH="x86_64"
        ;;
    aarch64|arm64)
        ARCH="arm64"
        ;;
    *)
        echo "❌ Unsupported architecture: $ARCH"
        exit 1
        ;;
esac

# Download and install act
echo "📥 Downloading act for $ARCH..."
curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Verify installation
if command -v act &> /dev/null; then
    echo "✅ Act installed successfully!"
    act --version
    
    echo ""
    echo "🚀 Usage examples:"
    echo "  act                    # Run all workflows"
    echo "  act push               # Run push event workflows"
    echo "  act pull_request       # Run PR workflows"
    echo "  act -j test-and-quality # Run specific job"
    echo "  act --dry-run          # Show what would run"
    echo "  act -l                 # List all workflows"
    
    echo ""
    echo "📖 To run your CI/CD pipeline:"
    echo "  cd $(pwd)"
    echo "  act push"
    
else
    echo "❌ Act installation failed"
    exit 1
fi