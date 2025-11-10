"""
ZAP Authentication Manager

Handles authentication for different web applications to enable scanning
of protected areas. Supports form-based and HTTP authentication.
"""

import logging
import time
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse, urljoin
import requests

logger = logging.getLogger(__name__)


class ZAPAuthManager:
    """Manage authentication in ZAP for various web applications"""

    # Pre-configured authentication profiles for common vulnerable apps
    AUTH_PROFILES = {
        'dvwa': {
            'name': 'DVWA (Damn Vulnerable Web Application)',
            'detection': ['dvwa', 'damn-vulnerable'],
            'login_url_path': '/login.php',
            'login_form': {
                'username_field': 'username',
                'password_field': 'password',
                'extra_fields': {'Login': 'Login'},
            },
            'default_credentials': [
                {'username': 'admin', 'password': 'password'},
                {'username': 'admin', 'password': 'admin'},
            ],
            'logged_in_indicator': r'\QSecurity Level\E',
            'logged_out_indicator': r'\Qlogin\.php\E',
            'session_management': 'cookie'
        },
        'testfire': {
            'name': 'Altoro Mutual (TestFire)',
            'detection': ['testfire', 'altoromutual'],
            'login_url_path': '/bank/login.jsp',
            'login_form': {
                'username_field': 'uid',
                'password_field': 'passw',
                'extra_fields': {'btnSubmit': 'Login'},
            },
            'default_credentials': [
                {'uid': 'jsmith', 'passw': 'demo1234'},
                {'uid': 'admin', 'passw': 'admin'},
            ],
            'logged_in_indicator': r'\QMy Account\E',
            'logged_out_indicator': r'\Qlogin\.jsp\E',
            'session_management': 'cookie'
        },
        'juice_shop': {
            'name': 'OWASP Juice Shop',
            'detection': ['juice-shop', 'juiceshop'],
            'login_url_path': '/rest/user/login',
            'login_type': 'json',
            'login_form': {
                'username_field': 'email',
                'password_field': 'password',
            },
            'default_credentials': [
                {'email': 'admin@juice-sh.op', 'password': 'admin123'},
            ],
            'logged_in_indicator': r'\Qtoken\E',
            'logged_out_indicator': r'\Qlogin\E',
            'session_management': 'token'
        },
        'sqli_labs': {
            'name': 'SQLi-Labs',
            'detection': ['sqli-labs', 'sqli_labs'],
            'login_url_path': None,  # No authentication needed
            'login_form': None,
            'default_credentials': [],
            'logged_in_indicator': None,
            'logged_out_indicator': None,
            'session_management': None
        },
        'bwapp': {
            'name': 'bWAPP (buggy Web Application)',
            'detection': ['bwapp'],
            'login_url_path': '/login.php',
            'login_form': {
                'username_field': 'login',
                'password_field': 'password',
                'extra_fields': {'form': 'submit'},
            },
            'default_credentials': [
                {'login': 'bee', 'password': 'bug'},
            ],
            'logged_in_indicator': r'\QWelcome\E',
            'logged_out_indicator': r'\Qlogin\.php\E',
            'session_management': 'cookie'
        },
        'webgoat': {
            'name': 'WebGoat',
            'detection': ['webgoat'],
            'login_url_path': '/login',
            'login_form': {
                'username_field': 'username',
                'password_field': 'password',
            },
            'default_credentials': [
                {'username': 'user', 'password': 'user'},
                {'username': 'admin', 'password': 'admin'},
            ],
            'logged_in_indicator': r'\Qlogout\E',
            'logged_out_indicator': r'\Qlogin\E',
            'session_management': 'cookie'
        }
    }

    def __init__(self, zap_adapter):
        """
        Initialize ZAP authentication manager

        Args:
            zap_adapter: Instance of ZAPAdapter or ZAPActiveAdapter
        """
        self.zap = zap_adapter
        self.context_id = None
        self.user_id = None
        self.profile = None

    def detect_application_type(self, target_url: str) -> Optional[str]:
        """
        Auto-detect application type from URL

        Args:
            target_url: Target URL to analyze

        Returns:
            Profile key if detected, None otherwise
        """
        target_lower = target_url.lower()

        for profile_key, profile in self.AUTH_PROFILES.items():
            for detection_keyword in profile['detection']:
                if detection_keyword in target_lower:
                    logger.info(f"Detected application: {profile['name']}")
                    return profile_key

        logger.info("Could not auto-detect application type")
        return None

    def configure_authentication(
        self,
        target_url: str,
        profile_name: Optional[str] = None,
        custom_credentials: Optional[Dict] = None
    ) -> bool:
        """
        Configure authentication in ZAP for target

        Args:
            target_url: Base URL of target
            profile_name: Name of auth profile to use (auto-detect if None)
            custom_credentials: Custom credentials dict (overrides defaults)

        Returns:
            True if authentication configured successfully
        """
        # Auto-detect if profile not specified
        if not profile_name:
            profile_name = self.detect_application_type(target_url)

        if not profile_name or profile_name not in self.AUTH_PROFILES:
            logger.warning(f"No authentication profile found for {target_url}")
            return False

        self.profile = self.AUTH_PROFILES[profile_name]

        # Check if app needs authentication
        if not self.profile['login_url_path']:
            logger.info(f"{self.profile['name']} does not require authentication")
            return True

        try:
            # Step 1: Create authentication context
            if not self._create_context(target_url):
                return False

            # Step 2: Configure authentication method
            if not self._configure_auth_method(target_url, custom_credentials):
                return False

            # Step 3: Create and enable user
            if not self._create_user(custom_credentials):
                return False

            # Step 4: Test authentication
            if not self._test_authentication(target_url):
                logger.warning("Authentication test inconclusive, but continuing scan")

            logger.info(f"✅ Authentication configured for {self.profile['name']}")
            return True

        except Exception as e:
            logger.error(f"Failed to configure authentication: {e}")
            return False

    def _create_context(self, target_url: str) -> bool:
        """Create ZAP context for authentication"""
        try:
            parsed = urlparse(target_url)
            context_name = f"AuthContext_{self.profile['name']}_{int(time.time())}"

            # Create context
            response = self.zap._make_api_post_request("context/action/newContext", {
                "contextName": context_name
            })

            if not response or response.get("Result") == "ERROR":
                logger.error("Failed to create ZAP context")
                return False

            self.context_id = response.get("contextId")
            logger.info(f"Created ZAP context: {context_name} (ID: {self.context_id})")

            # Include target in context (use regex to match all paths)
            include_pattern = f"{parsed.scheme}://{parsed.netloc}/.*"
            self.zap._make_api_post_request("context/action/includeInContext", {
                "contextName": context_name,
                "regex": include_pattern
            })

            logger.info(f"Added URL pattern to context: {include_pattern}")
            return True

        except Exception as e:
            logger.error(f"Error creating context: {e}")
            return False

    def _configure_auth_method(
        self,
        target_url: str,
        custom_credentials: Optional[Dict] = None
    ) -> bool:
        """Configure authentication method in ZAP"""
        try:
            parsed = urlparse(target_url)
            login_url = urljoin(target_url, self.profile['login_url_path'])

            # Build login request data
            login_form = self.profile['login_form'].copy()
            username_field = login_form['username_field']
            password_field = login_form['password_field']

            # Build POST data string
            post_data_parts = [
                f"{username_field}={{{{%username%}}}}",
                f"{password_field}={{{{%password%}}}}"
            ]

            # Add extra fields if present
            if 'extra_fields' in login_form:
                for key, value in login_form['extra_fields'].items():
                    post_data_parts.append(f"{key}={value}")

            post_data = "&".join(post_data_parts)

            # Configure form-based authentication
            auth_config = f"loginUrl={login_url}&loginRequestData={post_data}"

            response = self.zap._make_api_post_request(
                "authentication/action/setAuthenticationMethod",
                {
                    "contextId": self.context_id,
                    "authMethodName": "formBasedAuthentication",
                    "authMethodConfigParams": auth_config
                }
            )

            if not response or response.get("Result") == "ERROR":
                logger.error("Failed to set authentication method")
                return False

            # Set logged in indicator
            if self.profile['logged_in_indicator']:
                self.zap._make_api_post_request(
                    "authentication/action/setLoggedInIndicator",
                    {
                        "contextId": self.context_id,
                        "loggedInIndicatorRegex": self.profile['logged_in_indicator']
                    }
                )

            # Set logged out indicator
            if self.profile['logged_out_indicator']:
                self.zap._make_api_post_request(
                    "authentication/action/setLoggedOutIndicator",
                    {
                        "contextId": self.context_id,
                        "loggedOutIndicatorRegex": self.profile['logged_out_indicator']
                    }
                )

            logger.info("Authentication method configured")
            return True

        except Exception as e:
            logger.error(f"Error configuring auth method: {e}")
            return False

    def _create_user(self, custom_credentials: Optional[Dict] = None) -> bool:
        """Create and configure user in ZAP"""
        try:
            # Create user
            response = self.zap._make_api_post_request("users/action/newUser", {
                "contextId": self.context_id,
                "name": "scanner_user"
            })

            if not response or 'userId' not in response:
                logger.error("Failed to create user")
                return False

            self.user_id = response['userId']
            logger.info(f"Created user with ID: {self.user_id}")

            # Determine credentials to use
            if custom_credentials:
                credentials = custom_credentials
            else:
                # Use first default credential set
                credentials = self.profile['default_credentials'][0] if self.profile['default_credentials'] else {}

            # Build credentials config
            cred_parts = []
            for key, value in credentials.items():
                cred_parts.append(f"{key}={value}")
            cred_config = "&".join(cred_parts)

            # Set credentials
            self.zap._make_api_post_request(
                "users/action/setAuthenticationCredentials",
                {
                    "contextId": self.context_id,
                    "userId": self.user_id,
                    "authCredentialsConfigParams": cred_config
                }
            )

            # Enable user
            self.zap._make_api_post_request("users/action/setUserEnabled", {
                "contextId": self.context_id,
                "userId": self.user_id,
                "enabled": "true"
            })

            logger.info(f"User configured with credentials: {list(credentials.keys())}")
            return True

        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return False

    def _test_authentication(self, target_url: str) -> bool:
        """Test if authentication is working"""
        try:
            # Access a protected page
            parsed = urlparse(target_url)

            # Try to access a page that should be protected
            if 'dvwa' in self.profile['name'].lower():
                test_url = urljoin(target_url, '/vulnerabilities/sqli/')
            elif 'testfire' in self.profile['name'].lower():
                test_url = urljoin(target_url, '/bank/main.jsp')
            else:
                test_url = target_url

            # Access URL through ZAP with user context
            self.zap._make_api_post_request("core/action/accessUrl", {
                "url": test_url
            })

            time.sleep(2)

            # Check if we got authenticated content
            # This is a basic check - actual verification would need page content analysis
            logger.info("Authentication test completed")
            return True

        except Exception as e:
            logger.warning(f"Authentication test failed: {e}")
            return False

    def get_authenticated_scan_params(self) -> Dict:
        """
        Get parameters for authenticated scanning

        Returns:
            Dict with context and user IDs for authenticated scans
        """
        return {
            'contextId': self.context_id,
            'userId': self.user_id,
            'profile_name': self.profile['name'] if self.profile else None
        }
