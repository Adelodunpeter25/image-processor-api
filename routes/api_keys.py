"""API Key management routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from models.user import db
from models.api_key import APIKey
from middleware.auth import get_current_user
from middleware.api_auth import api_key_or_jwt_required
import secrets

api_keys_bp = Blueprint('api_keys', __name__)

def generate_api_key():
    """Generate a secure API key."""
    random_part = secrets.token_hex(16)  # 32 characters
    return f"sk_live_{random_part}"

@api_keys_bp.route('', methods=['POST'])
@jwt_required()
def create_api_key():
    """Generate a new API key for the authenticated user."""
    try:
        user = get_current_user()
        data = request.get_json()
        
        if not data or 'name' not in data:
            return jsonify({'error': 'Key name is required'}), 400
        
        name = data['name'].strip()
        
        if not name or len(name) > 100:
            return jsonify({'error': 'Name must be between 1 and 100 characters'}), 400
        
        # Check if user has too many keys
        existing_keys = APIKey.query.filter_by(user_id=user.id, is_active=True).count()
        if existing_keys >= 10:
            return jsonify({'error': 'Maximum 10 active API keys allowed'}), 400
        
        # Generate API key
        api_key = generate_api_key()
        prefix = f"{api_key[:10]}...{api_key[-3:]}"
        
        # Create database record
        new_key = APIKey(
            name=name,
            prefix=prefix,
            user_id=user.id
        )
        new_key.set_key(api_key)
        
        db.session.add(new_key)
        db.session.commit()
        
        return jsonify({
            'message': 'API key created successfully',
            'api_key': api_key,  # Shown only once!
            'id': new_key.id,
            'name': new_key.name,
            'prefix': prefix,
            'created_at': new_key.created_at.isoformat(),
            'warning': 'Store this key securely. It will not be shown again.'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create API key', 'message': str(e)}), 500

@api_keys_bp.route('', methods=['GET'])
@api_key_or_jwt_required
def list_api_keys():
    """List all API keys for the authenticated user."""
    try:
        user = get_current_user()
        
        keys = APIKey.query.filter_by(user_id=user.id).order_by(APIKey.created_at.desc()).all()
        
        return jsonify({
            'keys': [{
                'id': key.id,
                'name': key.name,
                'prefix': key.prefix,
                'created_at': key.created_at.isoformat(),
                'last_used': key.last_used.isoformat() if key.last_used else None,
                'is_active': key.is_active,
                'request_count': key.request_count
            } for key in keys]
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to list API keys', 'message': str(e)}), 500

@api_keys_bp.route('/<int:key_id>', methods=['DELETE'])
@jwt_required()
def revoke_api_key(key_id):
    """Revoke (deactivate) an API key."""
    try:
        user = get_current_user()
        
        api_key = APIKey.query.filter_by(id=key_id, user_id=user.id).first()
        
        if not api_key:
            return jsonify({'error': 'API key not found'}), 404
        
        api_key.is_active = False
        db.session.commit()
        
        return jsonify({'message': 'API key revoked successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to revoke API key', 'message': str(e)}), 500
