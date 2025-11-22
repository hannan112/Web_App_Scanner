#!/usr/bin/env python
"""
Quick test to verify the email notification fix is working
This checks if the Project model attribute is correctly referenced
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from projects.models import Project
from authentication.models import CustomUser

def test_project_owner_attribute():
    """Test that Project model has 'owner' attribute"""
    print("Testing Project model attributes...")
    
    # Check if Project has 'owner' field
    if hasattr(Project, 'owner'):
        print("✅ Project model has 'owner' attribute")
    else:
        print("❌ Project model does NOT have 'owner' attribute")
        return False
    
    # Check if Project has 'user' field (should NOT exist)
    if hasattr(Project, 'user'):
        print("⚠️  WARNING: Project model has 'user' attribute (unexpected)")
    else:
        print("✅ Project model does NOT have 'user' attribute (correct)")
    
    # Try to get a project and access its owner
    try:
        project = Project.objects.first()
        if project:
            print(f"\n✅ Found project: {project.name}")
            print(f"✅ Project owner: {project.owner.email}")
            print(f"✅ Owner username: {project.owner.username}")
            return True
        else:
            print("\n⚠️  No projects found in database")
            return True
    except Exception as e:
        print(f"\n❌ Error accessing project.owner: {e}")
        return False

if __name__ == "__main__":
    success = test_project_owner_attribute()
    sys.exit(0 if success else 1)
