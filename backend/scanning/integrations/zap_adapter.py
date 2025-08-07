# scanning/integrations/zap_adapter.py
import logging
from typing import Any, Dict, List

import requests

logger = logging.getLogger(__name__)


class ZAPAdapter:
    """Adapter for OWASP ZAP scanner integration using the UI API endpoint"""

    def __init__(self, config=None):
        self.config = config or {}
        self.host = self.config.get("zap_host", "localhost")
        self.port = self.config.get("zap_port", 8080)
        self.api_key = "changeme123"
        self.timeout = self.config.get("zap_timeout", 120)
        # Use the JSON endpoint instead of UI
        self.base_url = f"http://{self.host}:{self.port}/JSON"

    def initialize(self) -> bool:
        """Initialize connection to ZAP"""
        try:
            # Test connection with version API - use correct URL format
            url = f"{self.base_url}/core/view/version/"
            if self.api_key:
                url += f"?apikey={self.api_key}"

            # Add detailed logging
            logger.info(f"Attempting to connect to ZAP at: {url}")

            response = requests.get(url, timeout=10)

            logger.info(f"ZAP response status code: {response.status_code}")

            if response.status_code == 200:
                try:
                    data = response.json()
                    version = data.get("version", "unknown")
                    logger.info(f"ZAP connection successful: version {version}")
                    return True
                except ValueError:
                    logger.warning(
                        f"ZAP returned non-JSON response: {response.text[:100]}"
                    )
                    return False
            else:
                logger.error(
                    f"ZAP API returned status code {response.status_code}: {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"Error initializing ZAP connection: {str(e)}")
            return False

    def check_headers(self, url: str) -> List[Dict[str, Any]]:
        """Check security headers using ZAP"""
        findings = []

        if not self.initialize():
            return [
                {
                    "name": "ZAP Connection Error",
                    "description": "Could not connect to ZAP. Check if ZAP is running and accessible.",
                    "severity": "info",
                    "url": url,
                    "confidence": 1.0,
                    "remediation": "Ensure ZAP is running and correctly configured.",
                }
            ]

        try:
            # First, access the URL through ZAP
            access_url = f"{self.base_url}/core/action/accessUrl/"
            params = {"url": url}
            if self.api_key:
                params["apikey"] = self.api_key

            access_response = requests.get(access_url, params=params, timeout=30)
            if access_response.status_code != 200:
                return [
                    {
                        "name": "ZAP Error Accessing URL",
                        "description": f"ZAP could not access the URL: {access_response.text}",
                        "severity": "info",
                        "url": url,
                        "confidence": 1.0,
                        "remediation": "Check ZAP proxy settings and ensure the URL is accessible.",
                    }
                ]

            # Wait a bit for passive scan to complete
            import time

            time.sleep(5)

            # Get passive scan results
            alerts_url = f"{self.base_url}/core/view/alerts/"
            alerts_params = {"baseurl": url}
            if self.api_key:
                alerts_params["apikey"] = self.api_key

            alerts_response = requests.get(alerts_url, params=alerts_params, timeout=30)
            if alerts_response.status_code != 200:
                return [
                    {
                        "name": "ZAP Error Getting Alerts",
                        "description": f"ZAP could not retrieve alerts: {alerts_response.text}",
                        "severity": "info",
                        "url": url,
                        "confidence": 1.0,
                        "remediation": "Check ZAP configuration.",
                    }
                ]

            # Process alerts
            alerts_data = alerts_response.json()
            if "alerts" in alerts_data:
                for alert in alerts_data["alerts"]:
                    # Check if this is a header-related alert
                    if "header" in alert.get("name", "").lower():
                        findings.append(
                            {
                                "name": alert.get("name", "Header Issue"),
                                "description": alert.get("description", ""),
                                "severity": self._map_risk_to_severity(
                                    alert.get("risk", "")
                                ),
                                "url": url,
                                "confidence": self._map_confidence(
                                    alert.get("confidence", "")
                                ),
                                "remediation": alert.get("solution", ""),
                            }
                        )

            # If no findings but connection worked, return success indicator
            if not findings:
                findings.append(
                    {
                        "name": "ZAP Analysis Complete",
                        "description": "ZAP analyzed the URL but found no header issues.",
                        "severity": "info",
                        "url": url,
                        "confidence": 1.0,
                        "remediation": "None needed.",
                    }
                )

        except Exception as e:
            logger.error(f"Error checking headers with ZAP: {str(e)}")
            findings.append(
                {
                    "name": "ZAP Header Check Error",
                    "description": f"Error using ZAP to check headers: {str(e)}",
                    "severity": "info",
                    "url": url,
                    "confidence": 1.0,
                    "remediation": "Check ZAP configuration and try again.",
                }
            )

        return findings

    def _map_risk_to_severity(self, risk: str) -> str:
        """Map ZAP risk to severity level"""
        risk_map = {
            "High": "high",
            "Medium": "medium",
            "Low": "low",
            "Informational": "info",
        }
        return risk_map.get(risk, "info")

    def _map_confidence(self, confidence: str) -> float:
        """Map ZAP confidence to float value"""
        confidence_map = {"High": 0.9, "Medium": 0.7, "Low": 0.5}
        return confidence_map.get(confidence, 0.5)
