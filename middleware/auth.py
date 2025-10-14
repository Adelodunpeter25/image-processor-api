"""Authentication middleware for JWT token and API key verification."""
from functools import wraps
from flask import request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from models.user import User, db
from models.api_key import APIKey

def jwt_required_custom(fn):
    """Custom JWT decorator for route protection."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        return fn(*args, **kwargs)
    return wrapper

def get_current_user():
    """Get the current authenticated user from JWT token or API key."""
    # Check if user was set by API key
    if hasattr(request, 'current_user'):
        return request.current_user
    
    # Otherwise get from JWT
    user_id = get_jwt_identity()
    return User.query.get(int(user_id))

def get_user_from_api_key(api_key):
    """Get user from API key and track usage - optimized."""
    if not api_key or not api_key.startswith('sk_live_'):
        return None
    
    # Extract prefix for faster lookup (first 13 chars: "sk_live_" + first 5 of hash)
    prefix = f"{api_key[:10]}...{api_key[-3:]}"
    
    # Find key by prefix first (indexed lookup)
    key = APIKey.query.filter_by(prefix=prefix, is_active=True).first()
    
    if key and key.check_key(api_key):
        # Update usage stats asynchronously (don't block request)
        key.increment_usage()
        try:
            db.session.commit()
        except:
            db.session.rollback()  # Don't fail request if usage tracking fails
        
        return User.query.get(key.user_id)
    
    return None
