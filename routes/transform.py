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
