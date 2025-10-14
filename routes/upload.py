"""Image upload routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from models.user import db
from models.image import Image
from middleware.auth import get_current_user
from middleware.api_auth import api_key_or_jwt_required
from services.storage import StorageService
from services.processor import ImageProcessor
import os

upload_bp = Blueprint('upload', __name__)

def allowed_file(filename, allowed_extensions):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@upload_bp.route('/upload', methods=['POST'])
@api_key_or_jwt_required
def upload_image():
    """Upload an image file."""
    try:
        # Validate file presence
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type
        from main import app
        if not allowed_file(file.filename, app.config['ALLOWED_EXTENSIONS']):
            return jsonify({'error': 'Invalid file type. Allowed: png, jpg, jpeg, gif, webp'}), 400
        
        # Get authenticated user
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Save file to storage
        from main import app
        storage = StorageService(app.config['UPLOAD_FOLDER'])
        filepath, filename = storage.save_file(file, user.id)
        
        # Extract image metadata
        try:
            info = ImageProcessor.get_image_info(filepath)
        except Exception as e:
            storage.delete_file(filepath)
            return jsonify({'error': 'Invalid image file', 'message': str(e)}), 400
        
        # Save image metadata to database
        image = Image(
            user_id=user.id,
            filename=filename,
            original_path=filepath,
            format=info['format'],
            size=os.path.getsize(filepath),
            width=info['width'],
            height=info['height']
        )
        db.session.add(image)
        db.session.commit()
        
        return jsonify({
            'message': 'Image uploaded successfully',
            'image_id': image.id,
            'filename': filename,
            'format': info['format'],
            'width': info['width'],
            'height': info['height']
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Upload failed', 'message': str(e)}), 500
