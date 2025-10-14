"""Image transformation and retrieval routes."""
from flask import Blueprint, request, jsonify, send_file, redirect
from flask_jwt_extended import jwt_required
from models.image import Image
from models.user import db
from middleware.auth import get_current_user
from middleware.api_auth import api_key_or_jwt_required
from services.processor import ImageProcessor
import os
import requests
from io import BytesIO

transform_bp = Blueprint('transform', __name__)

def is_url(path):
    """Check if path is a URL."""
    return path.startswith('http://') or path.startswith('https://')

@transform_bp.route('/<int:image_id>', methods=['GET'])
@api_key_or_jwt_required
def get_image(image_id):
    """Retrieve original image by ID."""
    try:
        user = get_current_user()
        image = Image.query.filter_by(id=image_id, user_id=user.id).first()
        
        if not image:
            return jsonify({'error': 'Image not found'}), 404
        
        download = request.args.get('download', default='false').lower() == 'true'
        
        # If it's a URL (Supabase), redirect to it
        if is_url(image.original_path):
            return redirect(image.original_path)
        
        # Otherwise serve local file
        download_name = f"{image.filename}" if download else None
        return send_file(image.original_path, mimetype=f'image/{image.format}', as_attachment=download, download_name=download_name)
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve image', 'message': str(e)}), 500

@transform_bp.route('/<int:image_id>/transform', methods=['GET'])
@api_key_or_jwt_required
def transform_image(image_id):
    """Apply transformations to an image."""
    try:
        user = get_current_user()
        image = Image.query.filter_by(id=image_id, user_id=user.id).first()
        
        if not image:
            return jsonify({'error': 'Image not found'}), 404
        
        width = request.args.get('width', type=int)
        height = request.args.get('height', type=int)
        format = request.args.get('format', type=str)
        quality = request.args.get('quality', default=85, type=int)
        crop_x = request.args.get('crop_x', type=int)
        crop_y = request.args.get('crop_y', type=int)
        crop_width = request.args.get('crop_width', type=int)
        crop_height = request.args.get('crop_height', type=int)
        optimize = request.args.get('optimize', default='false').lower() == 'true'
        enhance = request.args.get('enhance', default='false').lower() == 'true'
        compress = request.args.get('compress', default='false').lower() == 'true'
        rotate = request.args.get('rotate', type=int)
        watermark_text = request.args.get('watermark', type=str)
        grayscale = request.args.get('grayscale', default='false').lower() == 'true'
        download = request.args.get('download', default='false').lower() == 'true'
        
        # Validation
        if quality and (quality < 1 or quality > 100):
            return jsonify({'error': 'Quality must be between 1 and 100'}), 400
        
        if width and width < 1:
            return jsonify({'error': 'Width must be positive'}), 400
        
        if height and height < 1:
            return jsonify({'error': 'Height must be positive'}), 400
        
        if format and format.lower() not in ['jpeg', 'jpg', 'png', 'webp']:
            return jsonify({'error': 'Invalid format. Allowed: jpeg, png, webp'}), 400
        
        if rotate and rotate not in [90, 180, 270, -90, -180, -270]:
            return jsonify({'error': 'Rotate must be 90, 180, or 270 degrees'}), 400
        
        # Get image path (download if URL)
        image_path = image.original_path
        if is_url(image_path):
            # Download from Supabase to process
            response = requests.get(image_path)
            image_path = BytesIO(response.content)
        
        buffer, output_format = ImageProcessor.transform_image(
            image_path, width, height, format, quality,
            crop_x, crop_y, crop_width, crop_height, optimize, enhance, compress, 
            rotate, watermark_text, grayscale
        )
        
        download_name = f"image_{image_id}.{output_format}" if download else None
        return send_file(buffer, mimetype=f'image/{output_format}', as_attachment=download, download_name=download_name)
    except Exception as e:
        return jsonify({'error': 'Transformation failed', 'message': str(e)}), 500

@transform_bp.route('/<int:image_id>/thumbnail', methods=['GET'])
@api_key_or_jwt_required
def get_thumbnail(image_id):
    """Generate thumbnail for an image."""
    try:
        user = get_current_user()
        image = Image.query.filter_by(id=image_id, user_id=user.id).first()
        
        if not image:
            return jsonify({'error': 'Image not found'}), 404
        
        download = request.args.get('download', default='false').lower() == 'true'
        size_param = request.args.get('size', default='150x150')
        try:
            width, height = map(int, size_param.split('x'))
            if width < 1 or height < 1 or width > 1000 or height > 1000:
                return jsonify({'error': 'Thumbnail size must be between 1x1 and 1000x1000'}), 400
            size = (width, height)
        except:
            return jsonify({'error': 'Invalid size format. Use format: WIDTHxHEIGHT (e.g., 150x150)'}), 400
        
        # Get image path (download if URL)
        image_path = image.original_path
        if is_url(image_path):
            response = requests.get(image_path)
            image_path = BytesIO(response.content)
        
        buffer, output_format = ImageProcessor.generate_thumbnail(image_path, size)
        
        download_name = f"thumbnail_{image_id}_{size_param}.{output_format}" if download else None
        return send_file(buffer, mimetype=f'image/{output_format}', as_attachment=download, download_name=download_name)
    except Exception as e:
        return jsonify({'error': 'Thumbnail generation failed', 'message': str(e)}), 500

@transform_bp.route('/<int:image_id>', methods=['DELETE'])
@api_key_or_jwt_required
def delete_image(image_id):
    """Delete an image and its file."""
    try:
        user = get_current_user()
        image = Image.query.filter_by(id=image_id, user_id=user.id).first()
        
        if not image:
            return jsonify({'error': 'Image not found'}), 404
        
        from services.storage import StorageService
        from main import app
        storage = StorageService(app.config['UPLOAD_FOLDER'])
        storage.delete_file(image.original_path)
        
        db.session.delete(image)
        db.session.commit()
        
        return jsonify({'message': 'Image deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Delete failed', 'message': str(e)}), 500

@transform_bp.route('/<int:image_id>/remove-background', methods=['GET'])
@api_key_or_jwt_required
def remove_background(image_id):
    """Remove background from an image."""
    try:
        user = get_current_user()
        image = Image.query.filter_by(id=image_id, user_id=user.id).first()
        
        if not image:
            return jsonify({'error': 'Image not found'}), 404
        
        format = request.args.get('format', type=str)
        download = request.args.get('download', default='false').lower() == 'true'
        
        # Validate format
        if format and format.lower() not in ['png', 'webp']:
            return jsonify({'error': 'Invalid format. Recommended: png (for transparency)'}), 400
        
        # Get image path (download if URL)
        image_path = image.original_path
        if is_url(image_path):
            response = requests.get(image_path)
            image_path = BytesIO(response.content)
        
        buffer, output_format = ImageProcessor.remove_background(image_path, format)
        
        download_name = f"no_bg_{image_id}.{output_format}" if download else None
        return send_file(buffer, mimetype=f'image/{output_format}', as_attachment=download, download_name=download_name)
    except Exception as e:
        return jsonify({'error': 'Background removal failed', 'message': str(e)}), 500

@transform_bp.route('', methods=['GET'])
@api_key_or_jwt_required
def list_images():
    """List all images for the authenticated user."""
    try:
        user = get_current_user()
        images = Image.query.filter_by(user_id=user.id).all()
        
        return jsonify({
            'images': [{
                'id': img.id,
                'filename': img.filename,
                'format': img.format,
                'width': img.width,
                'height': img.height,
                'size': img.size,
                'created_at': img.created_at.isoformat()
            } for img in images]
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to list images', 'message': str(e)}), 500
