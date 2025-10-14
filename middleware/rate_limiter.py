"""Custom rate limiter for API keys and JWT tokens."""
from flask import request, jsonify
from functools import wraps
from datetime import datetime, timedelta
from collections import defaultdict
import threading

# In-memory storage for rate limiting (use Redis in production)
api_key_requests = defaultdict(list)
jwt_requests = defaultdict(list)
lock = threading.Lock()

# Rate limits
API_KEY_LIMITS = {
    'per_minute': 10,
    'per_hour': 100,
    'per_day': 10000
}

JWT_LIMITS = {
    'per_minute': 20,
    'per_hour': 200,
    'per_day': 2000
}

def clean_old_requests(requests_list, window_seconds):
    """Remove requests older than the time window."""
    cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)
    return [req_time for req_time in requests_list if req_time > cutoff]

def check_rate_limit(identifier, limits, is_api_key=False):
    """Check if request is within rate limits."""
    with lock:
        storage = api_key_requests if is_api_key else jwt_requests
        
        # Clean old requests
        storage[identifier] = clean_old_requests(storage[identifier], 86400)  # 24 hours
        
        now = datetime.utcnow()
        requests_list = storage[identifier]
        
        # Check per-minute limit
        minute_ago = now - timedelta(minutes=1)
        minute_requests = sum(1 for req in requests_list if req > minute_ago)
        if minute_requests >= limits['per_minute']:
            return False, f"Rate limit exceeded: {limits['per_minute']} requests per minute"
        
        # Check per-hour limit
        hour_ago = now - timedelta(hours=1)
        hour_requests = sum(1 for req in requests_list if req > hour_ago)
        if hour_requests >= limits['per_hour']:
            return False, f"Rate limit exceeded: {limits['per_hour']} requests per hour"
        
        # Check per-day limit
        day_ago = now - timedelta(days=1)
        day_requests = sum(1 for req in requests_list if req > day_ago)
        if day_requests >= limits['per_day']:
            return False, f"Rate limit exceeded: {limits['per_day']} requests per day"
        
        # Add current request
        storage[identifier].append(now)
        
        return True, None

def rate_limit_by_auth():
    """Decorator for rate limiting based on authentication method."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Check for API key
            api_key = request.headers.get('X-API-Key')
            
            if api_key:
                # Rate limit by API key
                allowed, error_msg = check_rate_limit(api_key, API_KEY_LIMITS, is_api_key=True)
                if not allowed:
                    return jsonify({'error': error_msg}), 429
            else:
                # Rate limit by user ID from JWT
                from flask_jwt_extended import get_jwt_identity
                try:
                    user_id = get_jwt_identity()
                    allowed, error_msg = check_rate_limit(f"jwt_{user_id}", JWT_LIMITS, is_api_key=False)
                    if not allowed:
                        return jsonify({'error': error_msg}), 429
                except:
                    # If no JWT, rate limit by IP (fallback)
                    ip = request.remote_addr
                    allowed, error_msg = check_rate_limit(f"ip_{ip}", JWT_LIMITS, is_api_key=False)
                    if not allowed:
                        return jsonify({'error': error_msg}), 429
            
            return fn(*args, **kwargs)
        return wrapper
    return decorator
