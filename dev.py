#!/usr/bin/env python3
"""
Development helper script for Aslan Drive
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description="", check=True):
    """Run a shell command and print status"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"❌ {description} failed")
            if result.stderr:
                print(result.stderr)
            return False
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        return False

def main():
    """Main development script"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Aslan Drive Development Helper")
    parser.add_argument("command", choices=[
        "setup", "build", "test-basic", "docker-build", 
        "docker-up", "docker-down", "schema-gen", "clean"
    ], help="Command to run")
    
    args = parser.parse_args()
    
    print(f"🚀 Aslan Drive Development Helper")
    print(f"Running: {args.command}")
    print("-" * 40)
    
    if args.command == "setup":
        success = True
        success &= run_command("python3 -m venv venv", "Creating virtual environment")
        success &= run_command("./venv/bin/pip install -r requirements.txt", "Installing dependencies")
        if success:
            print("\n🎉 Setup complete! Activate venv with: source venv/bin/activate")
    
    elif args.command == "build":
        success = True
        success &= run_command("python3 tools/schema_generator.py", "Generating schema")
        success &= run_command("python3 -m py_compile services/data_ingestion/main.py", "Validating data_ingestion")
        success &= run_command("python3 -m py_compile services/md_provider/main.py", "Validating md_provider")
        success &= run_command("python3 -m py_compile services/health_check/main.py", "Validating health_check")
        if success:
            print("\n✅ Build successful")
    
    elif args.command == "test-basic":
        success = run_command("python3 test_basic.py", "Running basic tests")
        if success:
            print("\n🎉 Basic tests passed!")
    
    elif args.command == "docker-build":
        success = run_command("docker-compose build", "Building Docker images")
        if success:
            print("\n🐳 Docker images built successfully")
    
    elif args.command == "docker-up":
        success = run_command("docker-compose up -d", "Starting Docker services")
        if success:
            print("\n🚀 Services started!")
            print("📊 MD Provider API: http://localhost:8000")
            print("🗄️  PostgreSQL: localhost:5432")
    
    elif args.command == "docker-down":
        success = run_command("docker-compose down", "Stopping Docker services")
        if success:
            print("\n🛑 Services stopped")
    
    elif args.command == "schema-gen":
        success = run_command("python3 tools/schema_generator.py", "Generating schema files")
        if success:
            print("\n📋 Schema files generated in generated/")
    
    elif args.command == "clean":
        success = True
        success &= run_command("rm -rf generated/*", "Cleaning generated files")
        success &= run_command("mkdir -p generated", "Recreating generated directory")
        if success:
            print("\n🧹 Cleanup complete")

if __name__ == "__main__":
    main()