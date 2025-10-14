"""Batch processing routes for multiple images."""
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required
from models.image import Image
from models.user import db
from middleware.auth import get_current_user
from middleware.api_auth import api_key_or_jwt_required
from services.processor import ImageProcessor
from services.storage import StorageService
from werkzeug.utils import secure_filename
import os
import zipfile
from io import BytesIO
import requests

batch_bp = Blueprint('batch', __name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

storage_service = StorageService(UPLOAD_FOLDER)

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_url(path):
    """Check if path is a URL."""
    return path.startswith('http://') or path.startswith('https://')

@batch_bp.route('/upload', methods=['POST'])
@api_key_or_jwt_required
def batch_upload():
    """Upload multiple images at once."""
    try:
        user = get_current_user()
        
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        
        if not files or len(files) == 0:
            return jsonify({'error': 'No files selected'}), 400
        
        if len(files) > 10:
            return jsonify({'error': 'Maximum 10 files allowed per batch'}), 400
        
        uploaded_images = []
        errors = []
        
        for file in files:
            if file.filename == '':
                errors.append({'filename': 'empty', 'error': 'Empty filename'})
                continue
            
            if not allowed_file(file.filename):
                errors.append({'filename': file.filename, 'error': 'Invalid file type'})
                continue
            
            try:
                # Save file
                filepath, unique_filename = storage_service.save_file(file, user.id)
                
                # Get image format
                file_ext = file.filename.rsplit('.', 1)[1].lower()
                
                # Create database record
                new_image = Image(
                    filename=unique_filename,
                    original_path=filepath,
                    format=file_ext,
                    user_id=user.id
                )
                db.session.add(new_image)
                db.session.flush()
                
                uploaded_images.append({
                    'id': new_image.id,
                    'filename': unique_filename,
                    'format': file_ext
                })
                
            except Exception as e:
                errors.append({'filename': file.filename, 'error': str(e)})
        
        db.session.commit()
        
        return jsonify({
            'message': f'Uploaded {len(uploaded_images)} images',
            'images': uploaded_images,
            'errors': errors if errors else None
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Batch upload failed', 'message': str(e)}), 500

@batch_bp.route('/transform', methods=['POST'])
@api_key_or_jwt_required
def batch_transform():
    """Apply same transformation to multiple images."""
    try:
        user = get_current_user()
        data = request.get_json()
        
        if not data or 'image_ids' not in data:
            return jsonify({'error': 'image_ids required'}), 400
        
        image_ids = data['image_ids']
        
        if not isinstance(image_ids, list) or len(image_ids) == 0:
            return jsonify({'error': 'image_ids must be a non-empty array'}), 400
        
        if len(image_ids) > 10:
            return jsonify({'error': 'Maximum 10 images per batch'}), 400
        
        # Get transformation parameters
        width = data.get('width')
        height = data.get('height')
        format = data.get('format')
        quality = data.get('quality', 85)
        crop_x = data.get('crop_x')
        crop_y = data.get('crop_y')
        crop_width = data.get('crop_width')
        crop_height = data.get('crop_height')
        optimize = data.get('optimize', False)
        enhance = data.get('enhance', False)
        compress = data.get('compress', False)
        rotate = data.get('rotate')
        watermark_text = data.get('watermark')
        grayscale = data.get('grayscale', False)
        
        # Create ZIP file in memory
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for image_id in image_ids:
                image = Image.query.filter_by(id=image_id, user_id=user.id).first()
                
                if not image:
                    continue
                
                # Get image path (download if URL)
                image_path = image.original_path
                if is_url(image_path):
                    response = requests.get(image_path)
                    image_path = BytesIO(response.content)
                
                # Transform image
                buffer, output_format = ImageProcessor.transform_image(
                    image_path, width, height, format, quality,
                    crop_x, crop_y, crop_width, crop_height, optimize, enhance, compress,
                    rotate, watermark_text, grayscale
                )
                
                # Add to ZIP
                filename = f"transformed_{image_id}.{output_format}"
                zip_file.writestr(filename, buffer.getvalue())
        
        zip_buffer.seek(0)
        
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name='batch_transformed.zip'
        )
        
    except Exception as e:
        return jsonify({'error': 'Batch transformation failed', 'message': str(e)}), 500

@batch_bp.route('/remove-background', methods=['POST'])
@api_key_or_jwt_required
def batch_remove_background():
    """Remove background from multiple images."""
    try:
        user = get_current_user()
        data = request.get_json()
        
        if not data or 'image_ids' not in data:
            return jsonify({'error': 'image_ids required'}), 400
        
        image_ids = data['image_ids']
        
        if not isinstance(image_ids, list) or len(image_ids) == 0:
            return jsonify({'error': 'image_ids must be a non-empty array'}), 400
        
        if len(image_ids) > 10:
            return jsonify({'error': 'Maximum 10 images per batch'}), 400
        
        format = data.get('format', 'png')
        
        # Create ZIP file in memory
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for image_id in image_ids:
                image = Image.query.filter_by(id=image_id, user_id=user.id).first()
                
                if not image:
                    continue
                
                # Get image path (download if URL)
                image_path = image.original_path
                if is_url(image_path):
                    response = requests.get(image_path)
                    image_path = BytesIO(response.content)
                
                # Remove background
                buffer, output_format = ImageProcessor.remove_background(image_path, format)
                
                # Add to ZIP
                filename = f"no_bg_{image_id}.{output_format}"
                zip_file.writestr(filename, buffer.getvalue())
        
        zip_buffer.seek(0)
        
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name='batch_no_background.zip'
        )
        
    except Exception as e:
        return jsonify({'error': 'Batch background removal failed', 'message': str(e)}), 500
