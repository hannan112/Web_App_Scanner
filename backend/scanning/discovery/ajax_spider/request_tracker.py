# scanning/discovery/ajax_spider/request_tracker.py

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from playwright.async_api import Request, Response, Route

logger = logging.getLogger(__name__)


@dataclass
class TrackedRequest:
    url: str
    method: str
    headers: Dict[str, str]
    post_data: Optional[str]
    resource_type: str
    timestamp: str
    is_ajax: bool


@dataclass
class TrackedResponse:
    url: str
    status: int
    headers: Dict[str, str]
    timestamp: str


class RequestTracker:
    """Tracks network requests and responses"""
    
    def __init__(self):
        self.requests: List[TrackedRequest] = []
        self.responses: List[TrackedResponse] = []
        self.ajax_urls: List[str] = []
    
    async def setup_interception(self, context):
        """Set up request/response interception"""
        async def handle_route(route: Route):
            request = route.request
            await self._track_request(request)
            await route.continue_()
        
        # Intercept all requests
        await context.route('**/*', handle_route)
        
        # Track responses
        context.on('response', self._track_response)
    
    async def _track_request(self, request: Request):
        """Track individual request"""
        is_ajax = request.resource_type in ['xhr', 'fetch']
        
        tracked_request = TrackedRequest(
            url=request.url,
            method=request.method,
            headers=request.headers,
            post_data=request.post_data,
            resource_type=request.resource_type,
            timestamp=datetime.now().isoformat(),
            is_ajax=is_ajax
        )
        
        self.requests.append(tracked_request)
        
        if is_ajax:
            self.ajax_urls.append(request.url)
    
    def _track_response(self, response: Response):
        """Track individual response"""
        tracked_response = TrackedResponse(
            url=response.url,
            status=response.status,
            headers=response.headers,
            timestamp=datetime.now().isoformat()
        )
        
        self.responses.append(tracked_response)
    
    def get_ajax_urls(self) -> List[str]:
        """Get all AJAX/XHR URLs"""
        return list(set(self.ajax_urls))
    
    def get_results(self) -> Dict:
        """Get all tracked data"""
        return {
            'requests': [asdict(req) for req in self.requests],
            'responses': [asdict(resp) for resp in self.responses],
            'ajax_urls': self.get_ajax_urls(),
            'summary': {
                'total_requests': len(self.requests),
                'ajax_requests': len([r for r in self.requests if r.is_ajax]),
                'total_responses': len(self.responses)
            }
        }