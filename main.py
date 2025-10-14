"""
Image Processor API - Main application entry point.

A Flask-based image processing service with user authentication,
image upload, background removal and transformation capabilities.
"""
from flask import Flask, jsonify, send_from_directory
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_swagger_ui import get_swaggerui_blueprint
from config import Config
from models.user import db

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
jwt = JWTManager(app)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour", "10 per minute"],
    storage_uri="memory://"
)

# Swagger UI configuration
SWAGGER_URL = '/docs'
API_URL = '/swagger.json'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': "Image Processor API"}
)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

@app.route('/swagger.json')
def swagger_spec():
    """Serve the Swagger specification."""
    return send_from_directory('.', 'swagger.json')

@app.route('/', methods=['GET', 'HEAD'])
def home():
    """Serve as the home route."""
    return {
        "message": "Image Processor API", 
        "status": "running"
        }

# Register blueprints
from routes.auth import auth_bp
from routes.upload import upload_bp
from routes.transform import transform_bp

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(upload_bp, url_prefix='/api/images')
app.register_blueprint(transform_bp, url_prefix='/api/images')

# Global error handlers
@app.errorhandler(400)
def bad_request(e):
    """Handle bad request errors."""
    return jsonify({'error': 'Bad request', 'message': str(e)}), 400

@app.errorhandler(401)
def unauthorized(e):
    """Handle unauthorized access errors."""
    return jsonify({'error': 'Unauthorized', 'message': 'Invalid or missing authentication'}), 401

@app.errorhandler(404)
def not_found(e):
    """Handle not found errors."""
    return jsonify({'error': 'Not found', 'message': 'Resource not found'}), 404

@app.errorhandler(413)
def request_entity_too_large(e):
    """Handle file too large errors."""
    return jsonify({'error': 'File too large', 'message': 'Maximum file size is 16MB'}), 413

@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded errors."""
    return jsonify({'error': 'Rate limit exceeded', 'message': str(e.description)}), 429

@app.errorhandler(500)
def internal_error(e):
    """Handle internal server errors."""
    return jsonify({'error': 'Internal server error', 'message': 'An unexpected error occurred'}), 500

# Initialize database
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
