from django.core.management.base import BaseCommand
from projects.models import Project
from authentication.models import CustomUser

class Command(BaseCommand):
    help = 'Adds a list of vulnerable web applications to the database'

    def handle(self, *args, **kwargs):
        # Target user email
        user_email = "hannanhaxor686@gmail.com"
        
        try:
            user = CustomUser.objects.get(email=user_email)
        except CustomUser.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User with email {user_email} not found."))
            return

        targets = [
            {"name": "IBM Banking app (Testfire)", "url": "https://demo.testfire.net/"},
            {"name": "Classic web vulnerabilities (TestPHP)", "url": "http://testphp.vulnweb.com"},
            {"name": "bWAPP (Buggy Web Application)", "url": "http://www.itsecgames.com"},
            {"name": "PortSwigger Web Security Academy Labs", "url": "https://portswigger.net/web-security"},
            {"name": "Zero Bank", "url": "http://zero.webappsecurity.com"},
            {"name": "Google’s XSS Testing Ground", "url": "https://public-firing-range.appspot.com"},
            {"name": "HTML5/Modern web app vulnerabilities", "url": "http://testhtml5.vulnweb.com"},
            {"name": "Google Gruyere", "url": "https://google-gruyere.appspot.com/"},
            {"name": "OWASP WebGoat", "url": "https://webgoat.cloud/"},
            {"name": "OWASP WebWolf", "url": "https://webwolf.cloud/"},
            {"name": "Damn Vulnerable Web Application (DVWA)", "url": "https://dvwa.live/"},
            {"name": "Damn Vulnerable GraphQL API (DVGA)", "url": "https://graphql.security/dvga"},
            {"name": "HackThisSite", "url": "https://www.hackthissite.org/"},
            {"name": "Altoro Mutual", "url": "https://altoromutual.com/"},
            {"name": "OWASP Security Shepherd", "url": "https://owasp.org/www-project-security-shepherd/"},
            {"name": "OWASP NodeGoat", "url": "https://nodegoat.herokuapp.com"},
            {"name": "OWASP Damn Vulnerable Web Services", "url": "https://dvws.herokuapp.com"},
            {"name": "OWASP VulnerableApp Demo", "url": "https://vulnerableapp.dev/"},
            {"name": "Vulnweb Acunetix test site (ASP.NET)", "url": "http://testaspnet.vulnweb.com"},
            {"name": "Vulnweb Acunetix test site (ASP)", "url": "http://testasp.vulnweb.com"},
            {"name": "Peruggia", "url": "https://peruggia-open-source-demo.herokuapp.com"},
            {"name": "Hackazon", "url": "https://hackazon.webscantest.com/"},
            {"name": "WebScanTest vulnerable suite", "url": "https://pentesteracademylab.appspot.com/"},
        ]

        created_count = 0
        skipped_count = 0

        for target in targets:
            project, created = Project.objects.get_or_create(
                name=target["name"],
                owner=user,
                defaults={
                    "target_url": target["url"],
                    "description": f"Vulnerable target: {target['name']}"
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created project: {target['name']}"))
                created_count += 1
            else:
                # Update URL if name matches but URL might be different? 
                # For now, just skip if name matches for this user.
                if project.target_url != target["url"]:
                     self.stdout.write(self.style.WARNING(f"Project exists but URL mismatch for {target['name']}. Existing: {project.target_url}, New: {target['url']}"))
                else:
                    self.stdout.write(f"Skipped existing project: {target['name']}")
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(f"\nFinished. Created: {created_count}, Skipped: {skipped_count}"))
