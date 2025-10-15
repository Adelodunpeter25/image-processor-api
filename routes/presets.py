"""Preset transformation routes."""
from flask import Blueprint, request, jsonify, send_file
from models.user import db
from models.preset import Preset
from models.image import Image
from middleware.auth import get_current_user
from middleware.api_auth import api_key_or_jwt_required
from services.processor import ImageProcessor
import requests
from io import BytesIO

presets_bp = Blueprint('presets', __name__)

def is_url(path):
    """Check if path is a URL."""
    return path.startswith('http://') or path.startswith('https://')

@presets_bp.route('', methods=['POST'])
@api_key_or_jwt_required
def create_preset():
    """Create a new transformation preset."""
    try:
        user = get_current_user()
        data = request.get_json()
        
        if not data or 'name' not in data:
            return jsonify({'error': 'Preset name is required'}), 400
        
        name = data['name'].strip()
        if not name or len(name) > 100:
            return jsonify({'error': 'Name must be between 1 and 100 characters'}), 400
        
        # Check if preset name already exists for user
        existing = Preset.query.filter_by(user_id=user.id, name=name).first()
        if existing:
            return jsonify({'error': 'Preset with this name already exists'}), 400
        
        # Create preset
        preset = Preset(
            name=name,
            description=data.get('description', ''),
            user_id=user.id,
            is_public=data.get('is_public', False),
            width=data.get('width'),
            height=data.get('height'),
            format=data.get('format'),
            quality=data.get('quality'),
            crop_x=data.get('crop_x'),
            crop_y=data.get('crop_y'),
            crop_width=data.get('crop_width'),
            crop_height=data.get('crop_height'),
            rotate=data.get('rotate'),
            watermark=data.get('watermark'),
            optimize=data.get('optimize', False),
            enhance=data.get('enhance', False),
            compress=data.get('compress', False),
            grayscale=data.get('grayscale', False)
        )
        
        db.session.add(preset)
        db.session.commit()
        
        return jsonify({
            'message': 'Preset created successfully',
            'preset': preset.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create preset', 'message': str(e)}), 500

@presets_bp.route('', methods=['GET'])
@api_key_or_jwt_required
def list_presets():
    """List all presets (user's own + public presets)."""
    try:
        user = get_current_user()
        
        # Get user's own presets + public presets from others
        presets = Preset.query.filter(
            (Preset.user_id == user.id) | (Preset.is_public == True)
        ).order_by(Preset.created_at.desc()).all()
        
        return jsonify({
            'presets': [preset.to_dict() for preset in presets]
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to list presets', 'message': str(e)}), 500

@presets_bp.route('/<int:preset_id>', methods=['GET'])
@api_key_or_jwt_required
def get_preset(preset_id):
    """Get a specific preset."""
    try:
        user = get_current_user()
        
        preset = Preset.query.filter_by(id=preset_id).first()
        
        if not preset:
            return jsonify({'error': 'Preset not found'}), 404
        
        # Check access (own preset or public)
        if preset.user_id != user.id and not preset.is_public:
            return jsonify({'error': 'Access denied'}), 403
        
        return jsonify({'preset': preset.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get preset', 'message': str(e)}), 500

@presets_bp.route('/<int:preset_id>', methods=['PUT'])
@api_key_or_jwt_required
def update_preset(preset_id):
    """Update a preset."""
    try:
        user = get_current_user()
        data = request.get_json()
        
        preset = Preset.query.filter_by(id=preset_id, user_id=user.id).first()
        
        if not preset:
            return jsonify({'error': 'Preset not found'}), 404
        
        # Update fields
        if 'name' in data:
            preset.name = data['name'].strip()
        if 'description' in data:
            preset.description = data['description']
        if 'is_public' in data:
            preset.is_public = data['is_public']
        if 'width' in data:
            preset.width = data['width']
        if 'height' in data:
            preset.height = data['height']
        if 'format' in data:
            preset.format = data['format']
        if 'quality' in data:
            preset.quality = data['quality']
        if 'rotate' in data:
            preset.rotate = data['rotate']
        if 'watermark' in data:
            preset.watermark = data['watermark']
        if 'optimize' in data:
            preset.optimize = data['optimize']
        if 'enhance' in data:
            preset.enhance = data['enhance']
        if 'compress' in data:
            preset.compress = data['compress']
        if 'grayscale' in data:
            preset.grayscale = data['grayscale']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Preset updated successfully',
            'preset': preset.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update preset', 'message': str(e)}), 500

@presets_bp.route('/<int:preset_id>', methods=['DELETE'])
@api_key_or_jwt_required
def delete_preset(preset_id):
    """Delete a preset."""
    try:
        user = get_current_user()
        
        preset = Preset.query.filter_by(id=preset_id, user_id=user.id).first()
        
        if not preset:
            return jsonify({'error': 'Preset not found'}), 404
        
        db.session.delete(preset)
        db.session.commit()
        
        return jsonify({'message': 'Preset deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete preset', 'message': str(e)}), 500

@presets_bp.route('/<int:preset_id>/apply/<int:image_id>', methods=['GET'])
@api_key_or_jwt_required
def apply_preset(preset_id, image_id):
    """Apply a preset to an image."""
    try:
        user = get_current_user()
        
        # Get preset
        preset = Preset.query.filter_by(id=preset_id).first()
        if not preset:
            return jsonify({'error': 'Preset not found'}), 404
        
        # Check access
        if preset.user_id != user.id and not preset.is_public:
            return jsonify({'error': 'Access denied'}), 403
        
        # Get image
        image = Image.query.filter_by(id=image_id, user_id=user.id).first()
        if not image:
            return jsonify({'error': 'Image not found'}), 404
        
        # Get image path
        image_path = image.original_path
        if is_url(image_path):
            response = requests.get(image_path)
            image_path = BytesIO(response.content)
        
        # Apply preset transformations
        params = preset.get_params()
        download = request.args.get('download', default='false').lower() == 'true'
        
        buffer, output_format = ImageProcessor.transform_image(image_path, **params)
        
        # Increment usage count
        preset.usage_count += 1
        db.session.commit()
        
        download_name = f"preset_{preset.name}_{image_id}.{output_format}" if download else None
        return send_file(buffer, mimetype=f'image/{output_format}', as_attachment=download, download_name=download_name)
        
    except Exception as e:
        return jsonify({'error': 'Failed to apply preset', 'message': str(e)}), 500
