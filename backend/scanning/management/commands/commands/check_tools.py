"""
Django management command to check the availability of external security tools
"""

import shutil
import socket
import subprocess
import sys

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Check the availability of security tools used by the scanner"

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.NOTICE("Checking security tools availability...\n")
        )

        # Check SSLyze
        self.check_sslyze()

        # Check ZAP
        self.check_zap()

        # Check Nuclei
        self.check_nuclei()

        # Check Wappalyzer
        self.check_wappalyzer()

        self.stdout.write(self.style.SUCCESS("\nTool availability check completed."))

    def check_sslyze(self):
        """Check if SSLyze is available"""
        self.stdout.write("Checking SSLyze... ", ending="")
        sys.stdout.flush()

        try:
            import sslyze

            version = getattr(sslyze, "__version__", "unknown")
            self.stdout.write(self.style.SUCCESS(f"Available (version {version})"))
        except ImportError:
            self.stdout.write(self.style.ERROR("Not installed"))
            self.stdout.write("  Install with: pip install sslyze>=5.1.0")

    def check_zap(self):
        """Check if ZAP is available"""
        self.stdout.write("Checking OWASP ZAP... ", ending="")
        sys.stdout.flush()

        try:
            import zapv2

            # Try connecting to ZAP service (localhost:8080 by default)
            try:
                s = socket.socket()
                s.settimeout(2)
                s.connect(("localhost", 8080))
                s.close()
                self.stdout.write(self.style.SUCCESS("Available and running"))
            except Exception:
                self.stdout.write(
                    self.style.WARNING("API installed but service not running")
                )
                self.stdout.write("  Start ZAP service with: docker-compose up zap")
        except ImportError:
            self.stdout.write(self.style.ERROR("Not installed"))
            self.stdout.write("  Install with: pip install python-owasp-zap-v2.4")

    def check_nuclei(self):
        """Check if Nuclei is available"""
        self.stdout.write("Checking Nuclei... ", ending="")
        sys.stdout.flush()

        nuclei_path = shutil.which("nuclei")
        if not nuclei_path:
            self.stdout.write(self.style.ERROR("Not installed"))
            self.stdout.write(
                "  Install from: https://github.com/projectdiscovery/nuclei"
            )
            return

        try:
            # Check version
            process = subprocess.run(
                ["nuclei", "-version"], capture_output=True, text=True, timeout=5
            )
            if process.returncode == 0:
                version = process.stdout.strip()
                self.stdout.write(self.style.SUCCESS(f"Available ({version})"))

                # Check templates
                self.stdout.write("Checking Nuclei templates... ", ending="")
                process = subprocess.run(
                    ["nuclei", "-tl"], capture_output=True, text=True, timeout=5
                )
                if process.returncode == 0:
                    template_count = len(process.stdout.strip().split("\n"))
                    self.stdout.write(
                        self.style.SUCCESS(f"{template_count} templates found")
                    )
                else:
                    self.stdout.write(self.style.WARNING("Templates might be missing"))
                    self.stdout.write(
                        "  Update templates with: nuclei -update-templates"
                    )
            else:
                self.stdout.write(self.style.ERROR("Error checking version"))
                self.stdout.write(f"  Error: {process.stderr}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))

    def check_wappalyzer(self):
        """Check if Wappalyzer is available"""
        self.stdout.write("Checking Wappalyzer... ", ending="")
        sys.stdout.flush()

        try:
            from Wappalyzer import Wappalyzer

            version = getattr(Wappalyzer, "__version__", "unknown")
            self.stdout.write(
                self.style.SUCCESS(f"Available (Python package, version {version})")
            )
            return
        except ImportError:
            pass

        # Try Node.js package
        wappalyzer_path = shutil.which("wappalyzer")
        if wappalyzer_path:
            try:
                process = subprocess.run(
                    ["wappalyzer", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if process.returncode == 0:
                    version = process.stdout.strip()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Available (Node.js package, version {version})"
                        )
                    )
                    return
            except Exception:
                pass

        self.stdout.write(self.style.ERROR("Not installed"))
        self.stdout.write(
            "  Install Python package with: pip install python-Wappalyzer"
        )
        self.stdout.write("  Or Node.js package with: npm install -g wappalyzer")
