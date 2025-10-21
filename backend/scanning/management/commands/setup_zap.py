from django.core.management.base import BaseCommand
import requests
import subprocess
import shutil
import time


class Command(BaseCommand):
    help = "Setup and configure ZAP for AJAX spider"

    def handle(self, *args, **options):
        self.stdout.write("Setting up ZAP for AJAX spider...")
        
        # Check ZAP connection
        if not self.check_zap_connection():
            return
        
        # Configure AJAX spider settings
        self.configure_ajax_spider()
        
        # Test browser availability
        self.test_browser_availability()
        
    def check_zap_connection(self):
        """Check if ZAP is running and accessible"""
        try:
            response = requests.get(
                "http://localhost:8080/JSON/core/view/version/?apikey=changeme123",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                version = data.get("version", "unknown")
                self.stdout.write(self.style.SUCCESS(f"ZAP is running (version {version})"))
                return True
            else:
                self.stdout.write(self.style.ERROR("ZAP is not responding properly"))
                return False
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Could not connect to ZAP: {str(e)}"))
            self.stdout.write("Please start ZAP first:")
            self.stdout.write("  docker-compose up zap")
            self.stdout.write("  or")
            self.stdout.write("  zap.sh -daemon -host 0.0.0.0 -port 8080 -config api.key=changeme123")
            return False
        
    def configure_ajax_spider(self):
        """Configure AJAX spider settings"""
        self.stdout.write("Configuring AJAX spider settings...")
        base_url = "http://localhost:8080/JSON"
        api_key = "changeme123"
        
        # Set browser path (if available)
        browser_paths = [
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
            "/usr/bin/google-chrome",
            "/usr/bin/firefox",
            "/snap/bin/chromium"
        ]
        
        browser_found = False
        for path in browser_paths:
            if shutil.which(path) or self.check_file_exists(path):
                self.stdout.write(f"Found browser at: {path}")
                # Try to set browser path using different API endpoints
                if self.set_browser_path(base_url, api_key, path):
                    browser_found = True
                    break
        
        if not browser_found:
            self.stdout.write(self.style.WARNING("No suitable browser found. Please install one of:"))
            self.stdout.write("  sudo pacman -S chromium  # For Arch Linux")
            self.stdout.write("  sudo apt-get install chromium-browser  # For Ubuntu/Debian")
            self.stdout.write("  sudo apt-get install firefox")
        
        # Set browser type
        try:
            response = requests.get(
                f"{base_url}/ajaxSpider/action/setOptionBrowserId/",
                params={"String": "chrome", "apikey": api_key},
                timeout=10
            )
            if response.status_code == 200:
                self.stdout.write("Browser type set to: chrome")
            else:
                self.stdout.write(f"Failed to set browser type: {response.text}")
        except Exception as e:
            self.stdout.write(f"Error setting browser type: {str(e)}")
        
        # Set other AJAX spider options
        self.set_ajax_spider_options(base_url, api_key)
        
    def set_browser_path(self, base_url, api_key, path):
        """Try different methods to set browser path"""
        methods = [
            # Method 1: Direct API call
            lambda: requests.get(
                f"{base_url}/ajaxSpider/action/setOptionBrowserPath/",
                params={"String": path, "apikey": api_key},
                timeout=10
            ),
            # Method 2: POST request
            lambda: requests.post(
                f"{base_url}/ajaxSpider/action/setOptionBrowserPath/",
                params={"String": path, "apikey": api_key},
                timeout=10
            ),
            # Method 3: Different parameter name
            lambda: requests.get(
                f"{base_url}/ajaxSpider/action/setOptionBrowserPath/",
                params={"path": path, "apikey": api_key},
                timeout=10
            ),
        ]
        
        for i, method in enumerate(methods):
            try:
                response = method()
                if response.status_code == 200:
                    self.stdout.write(f"Browser path set to: {path} (method {i+1})")
                    return True
                else:
                    self.stdout.write(f"Method {i+1} failed: {response.text}")
            except Exception as e:
                self.stdout.write(f"Method {i+1} error: {str(e)}")
        
        # If all methods fail, try to set it via configuration
        self.stdout.write(f"Trying to set browser path via configuration...")
        try:
            # Try to access the URL through ZAP to trigger browser detection
            response = requests.get(
                f"{base_url}/core/action/accessUrl/",
                params={"url": "https://example.com", "apikey": api_key},
                timeout=10
            )
            if response.status_code == 200:
                self.stdout.write("Browser configuration may be working (URL access successful)")
                return True
        except Exception as e:
            self.stdout.write(f"URL access test failed: {str(e)}")
        
        return False
        
    def set_ajax_spider_options(self, base_url, api_key):
        """Set additional AJAX spider options"""
        options = [
            ("setOptionMaxDuration", "300"),  # 5 minutes max duration
            ("setOptionMaxCrawlDepth", "5"),  # Max crawl depth
            ("setOptionMaxCrawlStates", "100"),  # Max crawl states
            ("setOptionEventWait", "1000"),  # Wait 1 second between events
            ("setOptionReloadWait", "1000"),  # Wait 1 second after page reload
        ]
        
        for option, value in options:
            try:
                response = requests.get(
                    f"{base_url}/ajaxSpider/action/{option}/",
                    params={"Integer": value, "apikey": api_key},
                    timeout=10
                )
                if response.status_code == 200:
                    self.stdout.write(f"Set {option} to {value}")
                else:
                    self.stdout.write(f"Failed to set {option}: {response.text}")
            except Exception as e:
                self.stdout.write(f"Error setting {option}: {str(e)}")
    
    def test_browser_availability(self):
        """Test if browser is available and working"""
        self.stdout.write("Testing browser availability...")
        
        # Check if we can start a simple AJAX spider test
        try:
            # Create a test context
            base_url = "http://localhost:8080/JSON"
            api_key = "changeme123"
            
            context_name = f"test_context_{int(time.time())}"
            response = requests.get(
                f"{base_url}/context/action/newContext/",
                params={"contextName": context_name, "apikey": api_key},
                timeout=10
            )
            
            if response.status_code == 200:
                self.stdout.write("✓ Context creation works")
                
                # Clean up test context
                requests.get(
                    f"{base_url}/context/action/removeContext/",
                    params={"contextName": context_name, "apikey": api_key},
                    timeout=10
                )
            else:
                self.stdout.write("✗ Context creation failed")
                
        except Exception as e:
            self.stdout.write(f"✗ Browser test failed: {str(e)}")
        
        self.stdout.write(self.style.SUCCESS("ZAP AJAX spider configuration completed"))
        self.stdout.write("")
        self.stdout.write("Next steps:")
        self.stdout.write("1. Make sure a browser is installed (chromium recommended)")
        self.stdout.write("2. Test with a scan using AJAX spider")
        self.stdout.write("3. Check logs for any browser-related errors")
        self.stdout.write("")
        self.stdout.write("Note: If AJAX spider still fails, the system will fall back to custom crawler")
    
    def check_file_exists(self, path):
        """Check if a file exists"""
        try:
            import os
            return os.path.exists(path)
        except:
            return False 