"""Image upload routes."""
from flask import Blueprint, request, jsonify
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
        
        print(f"File uploaded - Path/URL: {filepath}")
        print(f"Filename: {filename}")
        
        # Extract image metadata
        try:
            # For URLs, download and get info from the file object
            if filepath.startswith('http'):
                import requests
                from io import BytesIO
                import time
                
                print(f"Attempting to download from: {filepath}")
                
                # Retry logic for Supabase (file might not be immediately available)
                max_retries = 3
                for attempt in range(max_retries):
                    response = requests.get(filepath)
                    print(f"Attempt {attempt + 1}: Status {response.status_code}")
                    if response.status_code == 200:
                        break
                    if attempt < max_retries - 1:
                        time.sleep(0.5)  # Wait 500ms before retry
                
                if response.status_code != 200:
                    print(f"Response headers: {response.headers}")
                    print(f"Response body: {response.text[:200]}")
                    raise Exception(f"Failed to download image: {response.status_code}")
                
                file_obj = BytesIO(response.content)
                file_obj.seek(0)
                
                # Verify we have content
                if len(response.content) == 0:
                    raise Exception("Downloaded file is empty")
                
                info = ImageProcessor.get_image_info(file_obj)
                file_size = len(response.content)
            else:
                # For local files
                info = ImageProcessor.get_image_info(filepath)
                file_size = os.path.getsize(filepath)
        except Exception as e:
            print(f"Error extracting image info: {e}")
            print(f"Filepath: {filepath}")
            storage.delete_file(filepath)
            return jsonify({'error': 'Invalid image file', 'message': str(e)}), 400
        
        # Save image metadata to database
        image = Image(
            user_id=user.id,
            filename=filename,
            original_path=filepath,
            format=info['format'],
            size=file_size,
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
