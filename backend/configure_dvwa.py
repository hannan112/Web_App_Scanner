#!/usr/bin/env python3
"""
DVWA Scanner Configuration Helper

This script helps configure the scanner for DVWA testing with optimized settings.
"""

import os
import sys
import django
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from projects.models import Project
from scanning.models.scan import ScanConfiguration


def configure_dvwa_project():
    """Configure a project for DVWA testing with optimized settings"""
    
    print("🔧 DVWA Scanner Configuration Helper")
    print("=" * 50)
    
    # Get or create DVWA project
    project_name = "DVWA Local Testing"
    target_url = "http://localhost:8005/index.php"  # Authenticated DVWA page
    
    try:
        project = Project.objects.get(name=project_name)
        print(f"✅ Found existing project: {project.name}")
    except Project.DoesNotExist:
        project = Project.objects.create(
            name=project_name,
            target_url=target_url,
            description="DVWA (Damn Vulnerable Web Application) for security testing"
        )
        print(f"✅ Created new project: {project.name}")
    
    # Update target URL to authenticated page
    if project.target_url != target_url:
        project.target_url = target_url
        project.save()
        print(f"✅ Updated target URL to: {target_url}")
    else:
        print(f"✅ Target URL already set to: {target_url}")
    
    # Create optimized scan configuration
    config_name = "DVWA Optimized Configuration"
    
    try:
        config = ScanConfiguration.objects.get(project=project, scan_type="comprehensive")
        print(f"✅ Found existing configuration: {config_name}")
    except ScanConfiguration.DoesNotExist:
        config = ScanConfiguration.objects.create(
            project=project,
            scan_type="comprehensive",
            description=config_name
        )
        print(f"✅ Created new configuration: {config_name}")
    
    # Apply optimized settings
    optimizations = {
        # Parameter fuzzing optimization
        "enable_parameter_fuzzing": True,
        "max_parameter_combinations": 20,  # Reduced from 50
        "max_parameters_per_url": 5,      # Reduced from 10
        "parameter_fuzzing_values": ["test", "admin", "1", "true", "false"],
        
        # Spider optimization
        "max_spider_duration": 180,       # 3 minutes instead of 5
        "max_spider_depth": 2,            # Reduced depth
        
        # SQLMap optimization
        "sqlmap_timeout": 30,             # Faster timeout
        "sqlmap_level": 1,                # Basic level
        "sqlmap_risk_level": 1,           # Low risk
        
        # Enhanced discovery limits
        "max_subdomains": 10,             # Reduced for local testing
        "max_wayback_urls": 50,           # Reduced
        "max_directories": 20,            # Reduced
        
        # Rate limiting
        "max_concurrent_requests": 3,      # Reduced for local testing
        "request_delay_ms": 200,          # Slightly slower for stability
    }
    
    print("\n🔧 Applying optimized settings:")
    for key, value in optimizations.items():
        if hasattr(config, key):
            setattr(config, key, value)
            print(f"  ✅ {key}: {value}")
        else:
            print(f"  ❌ {key}: Field not found")
    
    config.save()
    print(f"\n✅ Configuration saved successfully!")
    
    # Display summary
    print("\n📊 Configuration Summary:")
    print(f"  Project: {project.name}")
    print(f"  Target URL: {project.target_url}")
    print(f"  Scan Type: {config.scan_type}")
    print(f"  Parameter Fuzzing: {'Enabled' if config.enable_parameter_fuzzing else 'Disabled'}")
    print(f"  Max Parameter Combinations: {config.max_parameter_combinations}")
    print(f"  Max Parameters per URL: {config.max_parameters_per_url}")
    print(f"  Spider Duration: {config.max_spider_duration}s")
    print(f"  SQLMap Timeout: {config.sqlmap_timeout}s")
    
    print("\n🎯 Expected Results:")
    print("  • Reduced URL noise (from ~2,800 to ~200-500 URLs)")
    print("  • Faster scanning (3-5 minutes instead of 10+ minutes)")
    print("  • Focus on DVWA vulnerability pages")
    print("  • Better parameter testing with meaningful values")
    
    print(f"\n🚀 Ready to scan! Use project ID: {project.id}")
    
    return project.id, config.id


def show_scanning_tips():
    """Show tips for scanning DVWA"""
    print("\n💡 DVWA Scanning Tips:")
    print("  1. Make sure DVWA is running on http://localhost:8005")
    print("  2. Log into DVWA and navigate to index.php")
    print("  3. Set DVWA security level to 'Low' for testing")
    print("  4. Start with 'comprehensive' scan type")
    print("  5. Monitor the scan progress in the logs")
    print("  6. Check discovered URLs in /backend/logs/scan_XXX/")
    
    print("\n🔍 What to Expect:")
    print("  • /vulnerabilities/ - Main DVWA vulnerability sections")
    print("  • /setup.php - DVWA setup page")
    print("  • /login.php - Login page")
    print("  • Various vulnerability pages (brute, csrf, file inclusion, etc.)")


if __name__ == "__main__":
    try:
        project_id, config_id = configure_dvwa_project()
        show_scanning_tips()
        
        print(f"\n✅ Configuration complete!")
        print(f"   Project ID: {project_id}")
        print(f"   Config ID: {config_id}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


