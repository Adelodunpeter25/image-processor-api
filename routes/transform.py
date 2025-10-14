"""Image transformation and retrieval routes."""
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required
from models.image import Image
from models.user import db
from middleware.auth import get_current_user
from services.processor import ImageProcessor

transform_bp = Blueprint('transform', __name__)

@transform_bp.route('/<int:image_id>', methods=['GET'])
@jwt_required()
def get_image(image_id):
    """
    Retrieve original image by ID.
    ---
    tags:
      - Images
    security:
      - Bearer: []
    parameters:
      - in: path
        name: image_id
        type: integer
        required: true
    responses:
      200:
        description: Image file
      401:
        description: Unauthorized
      404:
        description: Image not found
      500:
        description: Server error
    """
    try:
        user = get_current_user()
        image = Image.query.filter_by(id=image_id, user_id=user.id).first()
        
        if not image:
            return jsonify({'error': 'Image not found'}), 404
        
        return send_file(image.original_path, mimetype=f'image/{image.format}')
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve image', 'message': str(e)}), 500

@transform_bp.route('/<int:image_id>/transform', methods=['GET'])
@jwt_required()
def transform_image(image_id):
    """
    Apply transformations to an image.
    ---
    tags:
      - Images
    security:
      - Bearer: []
    parameters:
      - in: path
        name: image_id
        type: integer
        required: true
      - in: query
        name: width
        type: integer
        description: Resize width
      - in: query
        name: height
        type: integer
        description: Resize height
      - in: query
        name: format
        type: string
        enum: [jpeg, png, webp]
        description: Output format
      - in: query
        name: quality
        type: integer
        default: 85
        description: Image quality (1-100)
      - in: query
        name: crop_x
        type: integer
        description: Crop starting X coordinate
      - in: query
        name: crop_y
        type: integer
        description: Crop starting Y coordinate
      - in: query
        name: crop_width
        type: integer
        description: Crop width
      - in: query
        name: crop_height
        type: integer
        description: Crop height
      - in: query
        name: rotate
        type: integer
        enum: [90, 180, 270, -90, -180, -270]
        description: Rotation angle
      - in: query
        name: watermark
        type: string
        description: Watermark text
      - in: query
        name: optimize
        type: boolean
        description: Enable optimization
      - in: query
        name: grayscale
        type: boolean
        description: Convert to grayscale
    responses:
      200:
        description: Transformed image
      400:
        description: Validation error
      401:
        description: Unauthorized
      404:
        description: Image not found
      429:
        description: Rate limit exceeded
      500:
        description: Server error
    """
    try:
        from main import limiter
        limiter.limit("20 per minute")(lambda: None)()
        
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
        rotate = request.args.get('rotate', type=int)
        watermark_text = request.args.get('watermark', type=str)
        grayscale = request.args.get('grayscale', default='false').lower() == 'true'
        
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
        
        buffer, output_format = ImageProcessor.transform_image(
            image.original_path, width, height, format, quality,
            crop_x, crop_y, crop_width, crop_height, optimize, rotate, watermark_text, grayscale
        )
        
        return send_file(buffer, mimetype=f'image/{output_format}')
    except Exception as e:
        return jsonify({'error': 'Transformation failed', 'message': str(e)}), 500

@transform_bp.route('/<int:image_id>/thumbnail', methods=['GET'])
@jwt_required()
def get_thumbnail(image_id):
    """
    Generate thumbnail for an image.
    ---
    tags:
      - Images
    security:
      - Bearer: []
    parameters:
      - in: path
        name: image_id
        type: integer
        required: true
      - in: query
        name: size
        type: string
        default: 150x150
        description: Thumbnail size (e.g., 150x150, 200x200)
    responses:
      200:
        description: Thumbnail image
      400:
        description: Validation error
      401:
        description: Unauthorized
      404:
        description: Image not found
      500:
        description: Server error
    """
    try:
        user = get_current_user()
        image = Image.query.filter_by(id=image_id, user_id=user.id).first()
        
        if not image:
            return jsonify({'error': 'Image not found'}), 404
        
        size_param = request.args.get('size', default='150x150')
        try:
            width, height = map(int, size_param.split('x'))
            if width < 1 or height < 1 or width > 1000 or height > 1000:
                return jsonify({'error': 'Thumbnail size must be between 1x1 and 1000x1000'}), 400
            size = (width, height)
        except:
            return jsonify({'error': 'Invalid size format. Use format: WIDTHxHEIGHT (e.g., 150x150)'}), 400
        
        buffer, output_format = ImageProcessor.generate_thumbnail(image.original_path, size)
        
        return send_file(buffer, mimetype=f'image/{output_format}')
    except Exception as e:
        return jsonify({'error': 'Thumbnail generation failed', 'message': str(e)}), 500

@transform_bp.route('/<int:image_id>', methods=['DELETE'])
@jwt_required()
def delete_image(image_id):
    """
    Delete an image and its file.
    ---
    tags:
      - Images
    security:
      - Bearer: []
    parameters:
      - in: path
        name: image_id
        type: integer
        required: true
    responses:
      200:
        description: Image deleted successfully
        schema:
          type: object
          properties:
            message:
              type: string
      401:
        description: Unauthorized
      404:
        description: Image not found
      500:
        description: Server error
    """
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

@transform_bp.route('', methods=['GET'])
@jwt_required()
def list_images():
    """
    List all images for the authenticated user.
    ---
    tags:
      - Images
    security:
      - Bearer: []
    responses:
      200:
        description: List of images
        schema:
          type: object
          properties:
            images:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  filename:
                    type: string
                  format:
                    type: string
                  width:
                    type: integer
                  height:
                    type: integer
                  size:
                    type: integer
                  created_at:
                    type: string
      401:
        description: Unauthorized
      500:
        description: Server error
    """
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
