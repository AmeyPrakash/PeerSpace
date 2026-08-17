"""
PeerSpace Security Headers Middleware
Applies CSP, HSTS, X-Frame-Options, nosniff, and strict referrer policy.
"""

from fastapi import Request

async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Prevent MIME type sniffing attacks
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    # Prevent clickjacking - disallow framing in any context
    response.headers["X-Frame-Options"] = "DENY"
    
    # Legacy XSS protection (modern browsers use CSP)
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # Strict referrer policy to limit referrer leakage
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Restrict which features can be used (microphone requires user gesture)
    response.headers["Permissions-Policy"] = "microphone=(self)"
    
    # HTTP Strict Transport Security - enforce HTTPS for 1 year
    # includeSubDomains ensures all subdomains use HTTPS
    # preload allows inclusion in HSTS preload lists
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains; preload"
    )
    
    # Content Security Policy - restrictive whitelist approach
    # Prevents XSS, clickjacking, and other injection attacks
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "  # unsafe-inline needed for dynamic styles, consider nonce approach
        "font-src 'self'; "
        "connect-src 'self' wss: ws:; "  # Allow WebSocket connections for voice chat
        "img-src 'self' data:; "
        "frame-ancestors 'none'; "  # Prevents framing more strictly than X-Frame-Options
        "base-uri 'self'; "  # Prevent base tag injection
        "form-action 'self'; "  # Restrict form submissions to same origin
        "upgrade-insecure-requests"  # Upgrade HTTP to HTTPS
    )
    
    # Additional security headers for defense-in-depth
    response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
    
    return response
