"""
Rate Limiting Middleware

Simple in-memory rate limiter for API protection.
In production, use Redis for distributed rate limiting.
"""

import time
from typing import Dict, Tuple
from fastapi import Request, HTTPException
from collections import defaultdict


class RateLimiter:
    """Simple token bucket rate limiter."""

    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)

    def _cleanup_old_requests(self, key: str, window: int = 60):
        """Remove requests older than the window."""
        now = time.time()
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if now - req_time < window
        ]

    def check_rate_limit(
        self,
        identifier: str,
        max_requests: int = 30,
        window: int = 60
    ) -> Tuple[bool, int]:
        """
        Check if request is within rate limit.
        Returns (is_allowed, requests_remaining)
        """
        self._cleanup_old_requests(identifier, window)

        current_count = len(self.requests[identifier])
        if current_count >= max_requests:
            return False, 0

        self.requests[identifier].append(time.time())
        return True, max_requests - current_count - 1


# Global rate limiter instance
rate_limiter = RateLimiter()


async def verify_rate_limit(request: Request, max_requests: int = 30):
    """FastAPI dependency to verify rate limit."""
    # Use client IP or forwarded header
    client_ip = request.headers.get("X-Forwarded-For", request.client.host)
    identifier = f"api_scan:{client_ip}"

    is_allowed, remaining = rate_limiter.check_rate_limit(identifier, max_requests)

    if not is_allowed:
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please try again later."
        )

    return {"remaining": remaining}