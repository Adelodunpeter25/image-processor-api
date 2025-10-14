"""Authentication middleware for JWT token verification."""
from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from models.user import User

def jwt_required_custom(fn):
    """Custom JWT decorator for route protection."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        return fn(*args, **kwargs)
    return wrapper

def get_current_user():
    """Get the current authenticated user from JWT token."""
    user_id = get_jwt_identity()
    return User.query.get(user_id)
