"""Decorator for API key or JWT authentication with rate limiting."""
from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from middleware.auth import get_user_from_api_key
from middleware.rate_limiter import check_rate_limit, API_KEY_LIMITS, JWT_LIMITS

def api_key_or_jwt_required(fn):
    """Decorator that accepts either API key or JWT token with rate limiting."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # Check for API key first
        api_key = request.headers.get('X-API-Key')
        
        if api_key:
            # Check API key rate limit
            allowed, error_msg = check_rate_limit(api_key, API_KEY_LIMITS, is_api_key=True)
            if not allowed:
                return jsonify({'error': error_msg}), 429
            
            # Authenticate with API key
            user = get_user_from_api_key(api_key)
            if user:
                request.current_user = user
                return fn(*args, **kwargs)
            else:
                return jsonify({'error': 'Invalid or inactive API key'}), 401
        
        # If no API key, require JWT
        try:
            verify_jwt_in_request()
            
            # Check JWT rate limit
            try:
                user_id = get_jwt_identity()
                allowed, error_msg = check_rate_limit(f"jwt_{user_id}", JWT_LIMITS, is_api_key=False)
                if not allowed:
                    return jsonify({'error': error_msg}), 429
            except Exception:
                # If can't get user_id, skip rate limiting for this request
                pass
            
            return fn(*args, **kwargs)
        except Exception:
            return jsonify({'error': 'Authentication required', 'message': 'Provide either X-API-Key header or JWT token'}), 401
    
    return wrapper
