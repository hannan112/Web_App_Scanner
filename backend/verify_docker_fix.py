
import logging
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_docker_stop_logic():
    print("Testing Docker container lookup logic...")
    
    try:
        import docker
        client = docker.from_env()
        
        # Find ZAP container dynamically (replicating the logic implemented)
        zap_container = None
        
        # Method 1: Try by exact name
        try:
            zap_container = client.containers.get('security_scanner_zap')
            print(f"Found by exact name: {zap_container.name}")
        except:
            print("Could not find by exact name 'security_scanner_zap'")
            
        # Method 2: Search by image name
        if not zap_container:
            for container in client.containers.list():
                if container.image.tags and 'zaproxy' in container.image.tags[0]:
                    zap_container = container
                    print(f"Found by image name: {zap_container.name}")
                    break
                    
        # Method 3: Search by name pattern
        if not zap_container:
            for container in client.containers.list():
                if 'zap' in container.name.lower():
                    zap_container = container
                    print(f"Found by name pattern: {zap_container.name}")
                    break
        
        if not zap_container:
            print("FAILURE: Could not find ZAP container!")
            return False

        print(f"SUCCESS: Found ZAP container: {zap_container.name} ({zap_container.id[:12]})")
        
        # Test exec_run (dry run - just check if we can execute 'true')
        print("Testing exec_run capability...")
        exit_code, output = zap_container.exec_run(["true"])
        
        if exit_code == 0:
            print("SUCCESS: Can execute commands in container")
            return True
        else:
            print(f"FAILURE: exec_run returned code {exit_code}")
            return False

    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    test_docker_stop_logic()
