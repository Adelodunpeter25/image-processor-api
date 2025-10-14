# Image Processor API

A Flask-based image processing service with user authentication, image upload, and transformation capabilities.

## Setup

1. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

## API Documentation

Interactive API documentation is available at:
- **Swagger UI**: http://localhost:5000/docs

The Swagger UI provides:
- Complete API endpoint documentation
- Request/response schemas
- Interactive testing interface
- Authentication support

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token

### Images
- `POST /api/images/upload` - Upload image
- `GET /api/images/<id>` - Get original image
- `GET /api/images/<id>/transform` - Get transformed image
- `GET /api/images/<id>/thumbnail` - Get thumbnail
- `DELETE /api/images/<id>` - Delete image
- `GET /api/images` - List all user images

### Transform Parameters
- `width` - Resize width
- `height` - Resize height
- `format` - Output format (jpeg, png, webp)
- `quality` - Image quality (1-100)
- `crop_x` - Crop starting X coordinate
- `crop_y` - Crop starting Y coordinate
- `crop_width` - Crop width
- `crop_height` - Crop height
- `rotate` - Rotation angle in degrees (e.g., 90, 180, 270)
- `watermark` - Watermark text to add to image
- `optimize` - Optimize image (true/false)
- `grayscale` - Convert to grayscale (true/false)

### Thumbnail Parameters
- `size` - Thumbnail size (e.g., 150x150, 200x200)

## Example Usage

```bash
# Register
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'

# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'

# Upload (use token from login)
curl -X POST http://localhost:5000/api/images/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@image.jpg"

# Transform
curl http://localhost:5000/api/images/1/transform?width=300&format=webp \
  -H "Authorization: Bearer <token>" \
  --output transformed.webp

# Crop and resize
curl "http://localhost:5000/api/images/1/transform?crop_x=100&crop_y=100&crop_width=500&crop_height=500&width=200" \
  -H "Authorization: Bearer <token>" \
  --output cropped.jpg

# Rotate image
curl "http://localhost:5000/api/images/1/transform?rotate=90" \
  -H "Authorization: Bearer <token>" \
  --output rotated.jpg

# Add watermark
curl "http://localhost:5000/api/images/1/transform?watermark=Copyright%202025" \
  -H "Authorization: Bearer <token>" \
  --output watermarked.jpg

# Optimize image
curl "http://localhost:5000/api/images/1/transform?optimize=true&quality=80" \
  -H "Authorization: Bearer <token>" \
  --output optimized.jpg

# Generate thumbnail
curl "http://localhost:5000/api/images/1/thumbnail?size=200x200" \
  -H "Authorization: Bearer <token>" \
  --output thumbnail.jpg
```
