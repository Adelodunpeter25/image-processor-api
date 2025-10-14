"""
Image Processor API - Main application entry point.

A Flask-based image processing service with user authentication,
image upload, background removal and transformation capabilities.
"""
import os
from flask import Flask, jsonify, send_from_directory
from flask_jwt_extended import JWTManager
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS
from dotenv import load_dotenv
from config import Config
from models.user import db

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

# Get environment
ENV = os.getenv('FLASK_ENV', 'development')
DEBUG = ENV == 'development'

# Initialize CORS
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-API-Key"],
        "expose_headers": ["Content-Disposition"]
    }
})

# Initialize extensions
db.init_app(app)
jwt = JWTManager(app)

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
    return jsonify({
        "message": "Image Processor API", 
        "description": "API for image upload, background removal, transformation, and management"
        })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "Image Processor API",
        "environment": ENV
    }), 200

# Register blueprints
from routes.auth import auth_bp
from routes.upload import upload_bp
from routes.transform import transform_bp
from routes.batch import batch_bp
from routes.api_keys import api_keys_bp

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(upload_bp, url_prefix='/api/images')
app.register_blueprint(transform_bp, url_prefix='/api/images')
app.register_blueprint(batch_bp, url_prefix='/api/batch')
app.register_blueprint(api_keys_bp, url_prefix='/api/auth/api-keys')

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
    # Import models to ensure they're registered
    from models.api_key import APIKey
    db.create_all()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Use Render’s assigned port
    if ENV == "production":
        print("🚀 Starting in PRODUCTION mode")
        app.run(host="0.0.0.0", port=port, debug=False)
    else:
        print("🔧 Starting in DEVELOPMENT mode")
        app.run(host="0.0.0.0", port=port, debug=True)