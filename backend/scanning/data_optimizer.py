"""
Data optimization utilities for handling large scan results
Specifically designed to handle large ZAP spider responses before sending to frontend
"""

import json
import logging
import gzip
from typing import Dict, List, Any, Optional, Tuple
from django.core.paginator import Paginator
import hashlib
import urllib.parse

logger = logging.getLogger(__name__)


class ScanDataOptimizer:
    """Optimizes large scan data for frontend consumption"""

    def __init__(self):
        self.max_urls_per_page = 100
        self.max_forms_per_page = 50
        self.max_evidence_length = 2000
        self.max_response_size_mb = 10  # 10MB limit for single response

    def optimize_spider_results(self, spider_data: Dict[str, Any],
                              page: int = 1, page_size: int = 100) -> Dict[str, Any]:
        """
        Optimize spider results by filtering, deduplication, and pagination

        Args:
            spider_data: Raw spider data from ZAP
            page: Page number for pagination
            page_size: Number of items per page

        Returns:
            Optimized spider data with pagination info
        """
        try:
            if not spider_data or not isinstance(spider_data, dict):
                return self._empty_spider_results()

            # Extract URLs and deduplicate
            urls = self._extract_and_deduplicate_urls(spider_data)

            # Filter out non-essential URLs
            filtered_urls = self._filter_important_urls(urls)

            # Paginate URLs
            paginated_urls = self._paginate_list(filtered_urls, page, page_size)

            # Extract forms and optimize
            forms = self._extract_and_optimize_forms(spider_data)

            # Calculate summary statistics
            stats = self._calculate_spider_stats(urls, forms)

            return {
                "urls": {
                    "data": paginated_urls["data"],
                    "pagination": paginated_urls["pagination"],
                    "total_discovered": len(urls),
                    "total_filtered": len(filtered_urls)
                },
                "forms": {
                    "data": forms[:20],  # Limit forms to top 20 most important
                    "total_count": len(forms)
                },
                "statistics": stats,
                "optimization_applied": True,
                "data_size_mb": self._calculate_size_mb(spider_data)
            }

        except Exception as e:
            logger.error(f"Error optimizing spider results: {str(e)}")
            return self._empty_spider_results()

    def optimize_ajax_spider_results(self, ajax_data: Dict[str, Any],
                                   page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        """
        Extract only useful, displayable information from AJAX spider results
        Focus on actionable security findings rather than raw data

        Args:
            ajax_data: Raw AJAX spider data from ZAP
            page: Page number for pagination
            page_size: Number of items per page

        Returns:
            Clean, displayable AJAX spider data with security-relevant information only
        """
        try:
            if not ajax_data or not isinstance(ajax_data, dict):
                return self._empty_ajax_results()

            # Extract only useful information for security analysis
            useful_endpoints = self._extract_security_relevant_endpoints(ajax_data)
            api_endpoints = self._extract_api_endpoints(ajax_data)
            dynamic_forms = self._extract_dynamic_forms(ajax_data)
            authentication_endpoints = self._extract_auth_endpoints(ajax_data)
            sensitive_data_exposure = self._check_sensitive_data_exposure(ajax_data)

            # Paginate the most important findings
            paginated_endpoints = self._paginate_list(useful_endpoints, page, page_size)

            return {
                "security_relevant_endpoints": paginated_endpoints,
                "api_endpoints": api_endpoints[:20],  # Top 20 API endpoints
                "dynamic_forms": dynamic_forms[:15],  # Top 15 dynamic forms
                "authentication_endpoints": authentication_endpoints[:10],  # Auth-related endpoints
                "sensitive_data_findings": sensitive_data_exposure[:10],  # Data exposure issues
                "summary": {
                    "total_endpoints_analyzed": len(useful_endpoints),
                    "api_endpoints_found": len(api_endpoints),
                    "dynamic_forms_found": len(dynamic_forms),
                    "auth_endpoints_found": len(authentication_endpoints),
                    "sensitive_data_issues": len(sensitive_data_exposure),
                    "optimization_applied": True
                },
                "pagination": paginated_endpoints.get("pagination", {}) if isinstance(paginated_endpoints, dict) else {}
            }

        except Exception as e:
            logger.error(f"Error optimizing AJAX spider results: {str(e)}")
            return self._empty_ajax_results()

    def optimize_vulnerabilities(self, vulnerabilities: List[Dict[str, Any]],
                               page: int = 1, page_size: int = 25) -> Dict[str, Any]:
        """
        Optimize vulnerability data for frontend display

        Args:
            vulnerabilities: List of vulnerability dictionaries
            page: Page number for pagination
            page_size: Number of items per page

        Returns:
            Optimized vulnerability data with pagination
        """
        try:
            if not vulnerabilities:
                return {"data": [], "pagination": {}, "summary": {}}

            # Sort by severity (critical -> high -> medium -> low -> info)
            severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
            sorted_vulns = sorted(vulnerabilities,
                                key=lambda x: severity_order.get(x.get("severity", "info"), 4))

            # Truncate evidence fields
            optimized_vulns = []
            for vuln in sorted_vulns:
                optimized_vuln = vuln.copy()
                if "evidence" in optimized_vuln:
                    evidence = optimized_vuln["evidence"]
                    if isinstance(evidence, str) and len(evidence) > self.max_evidence_length:
                        optimized_vuln["evidence"] = evidence[:self.max_evidence_length] + "... [truncated]"
                        optimized_vuln["evidence_truncated"] = True
                    elif isinstance(evidence, dict):
                        # Handle complex evidence objects
                        optimized_vuln["evidence"] = self._truncate_dict(evidence, max_depth=3)
                optimized_vulns.append(optimized_vuln)

            # Paginate results
            paginated_vulns = self._paginate_list(optimized_vulns, page, page_size)

            # Calculate summary
            summary = self._calculate_vulnerability_summary(vulnerabilities)

            return {
                "data": paginated_vulns["data"],
                "pagination": paginated_vulns["pagination"],
                "summary": summary
            }

        except Exception as e:
            logger.error(f"Error optimizing vulnerabilities: {str(e)}")
            return {"data": [], "pagination": {}, "summary": {}}

    def create_chunked_response(self, data: Dict[str, Any], chunk_size_mb: float = 2.0) -> List[Dict[str, Any]]:
        """
        Split large data into smaller chunks for progressive loading

        Args:
            data: Data to chunk
            chunk_size_mb: Maximum size per chunk in MB

        Returns:
            List of data chunks
        """
        try:
            data_size_mb = self._calculate_size_mb(data)

            if data_size_mb <= chunk_size_mb:
                return [data]

            chunks = []
            chunk_count = int(data_size_mb / chunk_size_mb) + 1

            # Split URLs if they exist
            if "urls" in data and "data" in data["urls"]:
                url_chunks = self._split_list_into_chunks(data["urls"]["data"], chunk_count)
                for i, url_chunk in enumerate(url_chunks):
                    chunk = data.copy()
                    chunk["urls"]["data"] = url_chunk
                    chunk["chunk_info"] = {
                        "chunk_number": i + 1,
                        "total_chunks": len(url_chunks),
                        "chunk_type": "urls"
                    }
                    chunks.append(chunk)
            else:
                # If no URL data, just return the original data
                chunks = [data]

            return chunks

        except Exception as e:
            logger.error(f"Error creating chunked response: {str(e)}")
            return [data]

    def compress_json_response(self, data: Dict[str, Any]) -> bytes:
        """
        Compress JSON data using gzip

        Args:
            data: Data to compress

        Returns:
            Compressed data as bytes
        """
        try:
            json_str = json.dumps(data, separators=(',', ':'), default=str)
            return gzip.compress(json_str.encode('utf-8'))
        except Exception as e:
            logger.error(f"Error compressing JSON response: {str(e)}")
            return json.dumps(data, default=str).encode('utf-8')

    def _extract_and_deduplicate_urls(self, spider_data: Dict[str, Any]) -> List[str]:
        """Extract and deduplicate URLs from spider data"""
        urls = set()

        # Handle different possible structures
        if "urls" in spider_data:
            if isinstance(spider_data["urls"], list):
                urls.update(spider_data["urls"])
            elif isinstance(spider_data["urls"], dict) and "data" in spider_data["urls"]:
                urls.update(spider_data["urls"]["data"])

        if "results" in spider_data:
            if isinstance(spider_data["results"], list):
                for result in spider_data["results"]:
                    if isinstance(result, str):
                        urls.add(result)
                    elif isinstance(result, dict) and "url" in result:
                        urls.add(result["url"])

        # Filter out invalid URLs
        valid_urls = []
        for url in urls:
            if self._is_valid_url(url):
                valid_urls.append(url)

        return sorted(valid_urls)

    def _filter_important_urls(self, urls: List[str]) -> List[str]:
        """Filter URLs to keep only the most important ones"""
        if len(urls) <= 500:  # If not too many URLs, keep all
            return urls

        important_urls = []
        less_important_urls = []

        for url in urls:
            if self._is_important_url(url):
                important_urls.append(url)
            else:
                less_important_urls.append(url)

        # Keep all important URLs + some less important ones
        max_less_important = max(0, 500 - len(important_urls))
        return important_urls + less_important_urls[:max_less_important]

    def _is_important_url(self, url: str) -> bool:
        """Determine if a URL is important for security testing"""
        important_patterns = [
            '/login', '/admin', '/api/', '/auth', '/upload', '/download',
            '/profile', '/settings', '/config', '/dashboard', '/panel',
            '?', '&', '=', '/search', '/form', '.php', '.asp', '.jsp'
        ]

        url_lower = url.lower()
        return any(pattern in url_lower for pattern in important_patterns)

    def _extract_and_optimize_forms(self, spider_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract and optimize form data"""
        forms = []

        if "forms" in spider_data:
            raw_forms = spider_data["forms"]
            if isinstance(raw_forms, list):
                for form in raw_forms:
                    if isinstance(form, dict):
                        optimized_form = {
                            "url": form.get("url", ""),
                            "method": form.get("method", "GET"),
                            "action": form.get("action", ""),
                            "fields_count": len(form.get("fields", [])),
                            "has_file_upload": any(
                                field.get("type") == "file"
                                for field in form.get("fields", [])
                            ),
                            "security_relevant": self._is_security_relevant_form(form)
                        }
                        forms.append(optimized_form)

        # Sort by security relevance
        return sorted(forms, key=lambda x: x.get("security_relevant", False), reverse=True)

    def _is_security_relevant_form(self, form: Dict[str, Any]) -> bool:
        """Check if a form is security-relevant"""
        url = form.get("url", "").lower()
        action = form.get("action", "").lower()
        fields = form.get("fields", [])

        # Check for login, registration, or other sensitive forms
        security_indicators = [
            "login", "password", "auth", "register", "admin", "upload", "delete"
        ]

        if any(indicator in url for indicator in security_indicators):
            return True

        if any(indicator in action for indicator in security_indicators):
            return True

        # Check field names
        for field in fields:
            field_name = str(field.get("name", "")).lower()
            field_type = str(field.get("type", "")).lower()
            if "password" in field_name or field_type in ["password", "file"]:
                return True

        return False

    def _extract_ajax_requests(self, ajax_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract AJAX requests from spider data"""
        requests = []

        if "results" in ajax_data and isinstance(ajax_data["results"], list):
            for result in ajax_data["results"]:
                if isinstance(result, dict):
                    request_info = {
                        "url": result.get("url", ""),
                        "method": result.get("method", "GET"),
                        "content_type": result.get("contentType", ""),
                        "response_code": result.get("code", 0),
                        "size": result.get("length", 0)
                    }
                    requests.append(request_info)

        return requests

    def _filter_ajax_requests(self, requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter AJAX requests to keep most relevant ones"""
        # Prioritize API endpoints, error responses, and large responses
        scored_requests = []

        for req in requests:
            score = 0
            url = req.get("url", "").lower()

            # Higher score for API endpoints
            if "/api/" in url or url.endswith(".json") or url.endswith(".xml"):
                score += 10

            # Higher score for error responses
            response_code = req.get("response_code", 200)
            if response_code >= 400:
                score += 5

            # Higher score for POST requests
            if req.get("method") == "POST":
                score += 3

            # Higher score for larger responses
            size = req.get("size", 0)
            if size > 10000:  # > 10KB
                score += 2

            scored_requests.append((score, req))

        # Sort by score and return top requests
        scored_requests.sort(key=lambda x: x[0], reverse=True)
        return [req for score, req in scored_requests[:200]]  # Limit to top 200

    def _extract_security_relevant_endpoints(self, ajax_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract security-relevant endpoints from AJAX data"""
        endpoints = []

        # Process different possible data structures from ZAP
        raw_results = ajax_data.get("results", [])
        if not isinstance(raw_results, list):
            raw_results = []

        for result in raw_results:
            if not isinstance(result, dict):
                continue

            # Extract URL and method information
            url = ""
            method = "GET"

            # Try different ways ZAP might structure the data
            if "url" in result:
                url = result["url"]
            elif "requestHeader" in result:
                # Parse URL from request header
                header = result["requestHeader"]
                if isinstance(header, str):
                    lines = header.split('\n')
                    if lines and lines[0]:
                        parts = lines[0].split(' ')
                        if len(parts) >= 2:
                            method = parts[0]
                            url = parts[1]

            if not url or not self._is_security_relevant_endpoint(url):
                continue

            endpoint_info = {
                "url": url,
                "method": method,
                "security_category": self._categorize_endpoint_security(url),
                "response_code": result.get("responseHeader", {}).get("statusCode", 0),
                "content_length": result.get("responseBody", {}).get("length", 0) if "responseBody" in result else 0,
                "discovered_by": "ajax_spider"
            }

            endpoints.append(endpoint_info)

        return sorted(endpoints, key=lambda x: self._security_priority(x["security_category"]))

    def _extract_api_endpoints(self, ajax_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract API endpoints from AJAX data"""
        api_endpoints = []

        raw_results = ajax_data.get("results", [])
        if not isinstance(raw_results, list):
            return []

        for result in raw_results:
            if not isinstance(result, dict):
                continue

            url = self._extract_url_from_result(result)
            if not url or not self._is_api_endpoint_url(url):
                continue

            method = self._extract_method_from_result(result)

            api_info = {
                "url": url,
                "method": method,
                "api_type": self._determine_api_type(url),
                "parameters": self._extract_parameters(url),
                "authentication_required": self._requires_authentication(url),
                "data_sensitivity": self._assess_data_sensitivity(url)
            }

            api_endpoints.append(api_info)

        return api_endpoints

    def _extract_dynamic_forms(self, ajax_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract dynamically discovered forms"""
        forms = []

        # Look for form-related AJAX calls
        raw_results = ajax_data.get("results", [])
        if not isinstance(raw_results, list):
            return []

        for result in raw_results:
            if not isinstance(result, dict):
                continue

            url = self._extract_url_from_result(result)
            method = self._extract_method_from_result(result)

            if not url:
                continue

            # Check if this looks like a form submission or form-related endpoint
            if self._is_form_related_endpoint(url, method):
                form_info = {
                    "action_url": url,
                    "method": method,
                    "form_type": self._classify_form_type(url),
                    "security_impact": self._assess_form_security_impact(url),
                    "discovered_via": "ajax_spider"
                }
                forms.append(form_info)

        return forms

    def _extract_auth_endpoints(self, ajax_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract authentication-related endpoints"""
        auth_endpoints = []

        raw_results = ajax_data.get("results", [])
        if not isinstance(raw_results, list):
            return []

        for result in raw_results:
            if not isinstance(result, dict):
                continue

            url = self._extract_url_from_result(result)
            if not url or not self._is_auth_endpoint(url):
                continue

            method = self._extract_method_from_result(result)

            auth_info = {
                "url": url,
                "method": method,
                "auth_type": self._classify_auth_type(url),
                "security_risk": self._assess_auth_risk(url, method),
                "requires_testing": True
            }

            auth_endpoints.append(auth_info)

        return auth_endpoints

    def _check_sensitive_data_exposure(self, ajax_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for potential sensitive data exposure"""
        exposures = []

        raw_results = ajax_data.get("results", [])
        if not isinstance(raw_results, list):
            return []

        for result in raw_results:
            if not isinstance(result, dict):
                continue

            url = self._extract_url_from_result(result)
            if not url:
                continue

            # Check response body for sensitive data patterns
            response_body = result.get("responseBody", {})
            if isinstance(response_body, dict) and "content" in response_body:
                content = str(response_body["content"])[:1000]  # First 1000 chars only

                sensitive_patterns = self._detect_sensitive_patterns(content)
                if sensitive_patterns:
                    exposure = {
                        "url": url,
                        "data_types_exposed": sensitive_patterns,
                        "severity": self._calculate_exposure_severity(sensitive_patterns),
                        "recommendation": "Review this endpoint for data exposure"
                    }
                    exposures.append(exposure)

        return exposures

    # Helper methods for the new extraction functions
    def _extract_url_from_result(self, result: Dict[str, Any]) -> str:
        """Extract URL from ZAP result object"""
        if "url" in result:
            return result["url"]
        elif "requestHeader" in result:
            header = result["requestHeader"]
            if isinstance(header, str):
                lines = header.split('\n')
                if lines and lines[0]:
                    parts = lines[0].split(' ')
                    if len(parts) >= 2:
                        return parts[1]
        return ""

    def _extract_method_from_result(self, result: Dict[str, Any]) -> str:
        """Extract HTTP method from ZAP result object"""
        if "method" in result:
            return result["method"]
        elif "requestHeader" in result:
            header = result["requestHeader"]
            if isinstance(header, str):
                lines = header.split('\n')
                if lines and lines[0]:
                    parts = lines[0].split(' ')
                    if len(parts) >= 1:
                        return parts[0]
        return "GET"

    def _is_security_relevant_endpoint(self, url: str) -> bool:
        """Check if endpoint is security-relevant"""
        url_lower = url.lower()
        security_patterns = [
            '/api/', '/admin', '/login', '/auth', '/user', '/profile',
            '/password', '/reset', '/token', '/session', '/upload',
            '/download', '/delete', '/create', '/update', '/config',
            '/settings', '/dashboard', '/panel', '/management'
        ]
        return any(pattern in url_lower for pattern in security_patterns)

    def _is_api_endpoint_url(self, url: str) -> bool:
        """Check if URL is an API endpoint"""
        url_lower = url.lower()
        api_indicators = ['/api/', '.json', '.xml', '/rest/', '/graphql', '/v1/', '/v2/']
        return any(indicator in url_lower for indicator in api_indicators)

    def _is_form_related_endpoint(self, url: str, method: str) -> bool:
        """Check if endpoint is form-related"""
        if method.upper() == "POST":
            return True
        url_lower = url.lower()
        form_patterns = ['form', 'submit', 'register', 'login', 'contact', 'feedback']
        return any(pattern in url_lower for pattern in form_patterns)

    def _is_auth_endpoint(self, url: str) -> bool:
        """Check if endpoint is authentication-related"""
        url_lower = url.lower()
        auth_patterns = ['login', 'auth', 'token', 'session', 'logout', 'signin', 'signup', 'register']
        return any(pattern in url_lower for pattern in auth_patterns)

    def _categorize_endpoint_security(self, url: str) -> str:
        """Categorize endpoint by security relevance"""
        url_lower = url.lower()

        if any(p in url_lower for p in ['/admin', '/management', '/config']):
            return "high_privilege"
        elif any(p in url_lower for p in ['/login', '/auth', '/password']):
            return "authentication"
        elif any(p in url_lower for p in ['/api/', '/rest/']):
            return "api_endpoint"
        elif any(p in url_lower for p in ['/upload', '/delete', '/create']):
            return "data_modification"
        else:
            return "general"

    def _security_priority(self, category: str) -> int:
        """Return priority score for security category"""
        priorities = {
            "high_privilege": 1,
            "authentication": 2,
            "data_modification": 3,
            "api_endpoint": 4,
            "general": 5
        }
        return priorities.get(category, 6)

    def _determine_api_type(self, url: str) -> str:
        """Determine the type of API"""
        url_lower = url.lower()
        if '/rest/' in url_lower or '/api/' in url_lower:
            return "REST API"
        elif '/graphql' in url_lower:
            return "GraphQL"
        elif '.json' in url_lower:
            return "JSON API"
        elif '.xml' in url_lower:
            return "XML API"
        else:
            return "Unknown API"

    def _extract_parameters(self, url: str) -> List[str]:
        """Extract parameters from URL"""
        if '?' not in url:
            return []

        query_string = url.split('?', 1)[1]
        params = []
        for param in query_string.split('&'):
            if '=' in param:
                param_name = param.split('=')[0]
                params.append(param_name)

        return params

    def _requires_authentication(self, url: str) -> bool:
        """Check if endpoint likely requires authentication"""
        url_lower = url.lower()
        protected_patterns = ['/user/', '/profile', '/account', '/dashboard', '/admin', '/private']
        return any(pattern in url_lower for pattern in protected_patterns)

    def _assess_data_sensitivity(self, url: str) -> str:
        """Assess data sensitivity level"""
        url_lower = url.lower()

        if any(p in url_lower for p in ['password', 'token', 'secret', 'key']):
            return "high"
        elif any(p in url_lower for p in ['user', 'profile', 'account', 'personal']):
            return "medium"
        else:
            return "low"

    def _classify_form_type(self, url: str) -> str:
        """Classify the type of form"""
        url_lower = url.lower()

        if 'login' in url_lower:
            return "login_form"
        elif any(p in url_lower for p in ['register', 'signup']):
            return "registration_form"
        elif 'upload' in url_lower:
            return "file_upload_form"
        elif 'contact' in url_lower:
            return "contact_form"
        else:
            return "generic_form"

    def _assess_form_security_impact(self, url: str) -> str:
        """Assess security impact of form"""
        url_lower = url.lower()

        if any(p in url_lower for p in ['login', 'auth', 'password']):
            return "high"
        elif 'upload' in url_lower:
            return "high"
        elif any(p in url_lower for p in ['register', 'signup', 'delete']):
            return "medium"
        else:
            return "low"

    def _classify_auth_type(self, url: str) -> str:
        """Classify authentication type"""
        url_lower = url.lower()

        if 'token' in url_lower:
            return "token_based"
        elif 'session' in url_lower:
            return "session_based"
        elif 'oauth' in url_lower:
            return "oauth"
        elif 'login' in url_lower:
            return "form_based"
        else:
            return "unknown"

    def _assess_auth_risk(self, url: str, method: str) -> str:
        """Assess authentication-related security risk"""
        url_lower = url.lower()

        if method.upper() == "GET" and any(p in url_lower for p in ['token', 'password']):
            return "high"  # Sensitive data in GET request
        elif 'reset' in url_lower and 'password' in url_lower:
            return "medium"  # Password reset functionality
        else:
            return "low"

    def _detect_sensitive_patterns(self, content: str) -> List[str]:
        """Detect sensitive data patterns in content"""
        import re

        patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
            "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            "api_key": r'\b[A-Za-z0-9]{32,}\b',
            "password": r'"password"\s*:\s*"[^"]{4,}"'
        }

        found_patterns = []
        for pattern_name, pattern_regex in patterns.items():
            if re.search(pattern_regex, content, re.IGNORECASE):
                found_patterns.append(pattern_name)

        return found_patterns

    def _calculate_exposure_severity(self, patterns: List[str]) -> str:
        """Calculate severity based on exposed data types"""
        high_risk = ['ssn', 'credit_card', 'password', 'api_key']
        medium_risk = ['email', 'phone']

        if any(pattern in high_risk for pattern in patterns):
            return "high"
        elif any(pattern in medium_risk for pattern in patterns):
            return "medium"
        else:
            return "low"

    def _is_api_endpoint(self, request: Dict[str, Any]) -> bool:
        """Check if a request is to an API endpoint"""
        url = request.get("url", "").lower()
        content_type = request.get("content_type", "").lower()

        return ("/api/" in url or
                url.endswith(".json") or
                url.endswith(".xml") or
                "application/json" in content_type or
                "application/xml" in content_type)

    def _paginate_list(self, items: List[Any], page: int, page_size: int) -> Dict[str, Any]:
        """Paginate a list of items"""
        if not items:
            return {
                "data": [],
                "pagination": {
                    "page": 1,
                    "page_size": page_size,
                    "total_items": 0,
                    "total_pages": 0,
                    "has_next": False,
                    "has_previous": False
                }
            }

        paginator = Paginator(items, page_size)
        page_obj = paginator.get_page(page)

        return {
            "data": list(page_obj),
            "pagination": {
                "page": page_obj.number,
                "page_size": page_size,
                "total_items": paginator.count,
                "total_pages": paginator.num_pages,
                "has_next": page_obj.has_next(),
                "has_previous": page_obj.has_previous()
            }
        }

    def _calculate_spider_stats(self, urls: List[str], forms: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate spider statistics"""
        url_extensions = {}
        url_params_count = 0
        secure_urls = 0

        for url in urls:
            # Count URLs with parameters
            if '?' in url:
                url_params_count += 1

            # Count secure URLs
            if url.startswith('https://'):
                secure_urls += 1

            # Count file extensions
            parsed = urllib.parse.urlparse(url)
            path = parsed.path.lower()
            if '.' in path:
                ext = path.split('.')[-1]
                url_extensions[ext] = url_extensions.get(ext, 0) + 1

        return {
            "total_urls": len(urls),
            "urls_with_parameters": url_params_count,
            "secure_urls": secure_urls,
            "total_forms": len(forms),
            "security_relevant_forms": len([f for f in forms if f.get("security_relevant")]),
            "file_extensions": dict(sorted(url_extensions.items(), key=lambda x: x[1], reverse=True)[:10])
        }

    def _calculate_vulnerability_summary(self, vulnerabilities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate vulnerability summary statistics"""
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        vuln_types = {}

        for vuln in vulnerabilities:
            severity = vuln.get("severity", "info")
            if severity in severity_counts:
                severity_counts[severity] += 1

            vuln_type = vuln.get("name", "Unknown")
            vuln_types[vuln_type] = vuln_types.get(vuln_type, 0) + 1

        return {
            "total": len(vulnerabilities),
            "by_severity": severity_counts,
            "top_types": dict(sorted(vuln_types.items(), key=lambda x: x[1], reverse=True)[:10])
        }

    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and should be included"""
        if not url or not isinstance(url, str):
            return False

        # Basic URL validation
        if not url.startswith(('http://', 'https://')):
            return False

        # Filter out obviously invalid or unwanted URLs
        unwanted_patterns = [
            'javascript:', 'mailto:', 'tel:', 'ftp://', 'file://',
            '.css', '.js', '.png', '.jpg', '.gif', '.ico', '.svg',
            '.pdf', '.doc', '.zip', '.tar', '.gz'
        ]

        url_lower = url.lower()
        return not any(pattern in url_lower for pattern in unwanted_patterns)

    def _calculate_size_mb(self, data: Any) -> float:
        """Calculate approximate size of data in MB"""
        try:
            json_str = json.dumps(data, default=str)
            size_bytes = len(json_str.encode('utf-8'))
            return size_bytes / (1024 * 1024)  # Convert to MB
        except:
            return 0.0

    def _split_list_into_chunks(self, items: List[Any], num_chunks: int) -> List[List[Any]]:
        """Split a list into roughly equal chunks"""
        if not items or num_chunks <= 0:
            return [items] if items else [[]]

        chunk_size = len(items) // num_chunks
        if chunk_size == 0:
            chunk_size = 1

        chunks = []
        for i in range(0, len(items), chunk_size):
            chunks.append(items[i:i + chunk_size])

        return chunks

    def _truncate_dict(self, data: Dict[str, Any], max_depth: int, current_depth: int = 0) -> Dict[str, Any]:
        """Recursively truncate dictionary content"""
        if current_depth >= max_depth:
            return {"...": "truncated"}

        truncated = {}
        for key, value in data.items():
            if isinstance(value, dict):
                truncated[key] = self._truncate_dict(value, max_depth, current_depth + 1)
            elif isinstance(value, list):
                truncated[key] = value[:10] if len(value) > 10 else value
            elif isinstance(value, str) and len(value) > 500:
                truncated[key] = value[:500] + "... [truncated]"
            else:
                truncated[key] = value

        return truncated

    def _empty_spider_results(self) -> Dict[str, Any]:
        """Return empty spider results structure"""
        return {
            "urls": {"data": [], "pagination": {}, "total_discovered": 0, "total_filtered": 0},
            "forms": {"data": [], "total_count": 0},
            "statistics": {},
            "optimization_applied": True,
            "error": "No spider data available"
        }

    def _empty_ajax_results(self) -> Dict[str, Any]:
        """Return empty AJAX results structure"""
        return {
            "ajax_requests": {"data": [], "pagination": {}},
            "javascript_interactions": [],
            "dynamic_content_discovered": 0,
            "optimization_applied": True,
            "error": "No AJAX spider data available"
        }