"""
PeerSpace Security: Sliding Window Rate Limiter with Brute Force Protection
Prevents abuse through distributed rate limiting with exponential backoff for admin endpoints.
"""

import time
from typing import Dict, Tuple
from fastapi import HTTPException, status

# Sliding window configuration
RATE_LIMIT_WINDOW = 60  # seconds
MAX_REQUESTS_PER_WINDOW = 30

# Brute force protection for admin endpoint
ADMIN_RATE_LIMIT_WINDOW = 300  # 5 minutes
MAX_ADMIN_ATTEMPTS = 10
admin_failed_attempts: Dict[str, Tuple[int, float]] = {}  # {client_id: (failure_count, last_attempt_time)}

request_logs: Dict[str, list] = {}

def check_rate_limit(client_id: str):
    """Enforces sliding window rate limit per client/session."""
    now = time.time()
    if client_id not in request_logs:
        request_logs[client_id] = []
    
    # Remove requests outside the window
    request_logs[client_id] = [t for t in request_logs[client_id] if now - t < RATE_LIMIT_WINDOW]
    
    # Check if limit exceeded
    if len(request_logs[client_id]) >= MAX_REQUESTS_PER_WINDOW:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please wait a moment before sending more messages."
        )
    
    request_logs[client_id].append(now)


def check_admin_rate_limit(client_id: str):
    """
    Enhanced rate limiting for admin authentication endpoint.
    Implements exponential backoff after multiple failed attempts.
    """
    now = time.time()
    
    # First, apply standard rate limiting
    check_rate_limit(client_id)
    
    # Check if client has exceeded failed attempts
    if client_id in admin_failed_attempts:
        failure_count, last_attempt = admin_failed_attempts[client_id]
        
        # Calculate exponential backoff: 2^(failures-1) seconds
        backoff_seconds = min(2 ** (failure_count - 1), 300)  # Cap at 5 minutes
        
        if now - last_attempt < backoff_seconds:
            wait_seconds = int(backoff_seconds - (now - last_attempt))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many failed attempts. Please try again in {wait_seconds} seconds."
            )
        
        # Reset counter if window has passed
        if now - last_attempt >= backoff_seconds:
            admin_failed_attempts[client_id] = (0, now)


def record_admin_auth_failure(client_id: str):
    """Record a failed admin authentication attempt."""
    now = time.time()
    
    if client_id not in admin_failed_attempts:
        admin_failed_attempts[client_id] = (1, now)
    else:
        failure_count, _ = admin_failed_attempts[client_id]
        admin_failed_attempts[client_id] = (failure_count + 1, now)
        
        # Block if exceeded max attempts
        if failure_count + 1 >= MAX_ADMIN_ATTEMPTS:
            backoff = 2 ** (failure_count) 
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Maximum authentication attempts exceeded. Account temporarily locked."
            )


def reset_admin_auth_attempts(client_id: str):
    """Reset failed attempts counter on successful authentication."""
    admin_failed_attempts.pop(client_id, None)
