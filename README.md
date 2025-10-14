# Image Processor API

A Flask-based image processing service with user authentication, image upload, background removal, and transformation capabilities.

## Features

- **User Authentication**: JWT-based authentication with registration and login
- **API Key Support**: Generate API keys for programmatic access
- **Image Upload**: Support for PNG, JPG, JPEG, GIF, WEBP formats (max 16MB)
- **Image Transformations**:
  - Resize (width/height)
  - Crop (custom dimensions)
  - Rotate (90, 180, 270 degrees)
  - Watermark (custom text)
  - Format conversion (JPEG, PNG, WebP)
  - Grayscale filter
  - Quality enhancement (sharpness, contrast, color)
  - Size-based compression
- **Background Removal**: AI-powered background removal
- **Configurable**: Environment-based configuration support
- **Thumbnail Generation**: Custom size thumbnails
- **Rate Limiting**: Protection against abuse
- **API Documentation**: Interactive Swagger UI

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

3. Create .env file:
```bash
cp .env.example .env
```

Edit `.env` and set your configuration:
```
FLASK_ENV=development  # or production
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret-key

# For production with Supabase storage:
PROJECT_URL=your-supabase-project-url
SERVICE_ROLE=your-supabase-service-role-key
SUPABASE_BUCKET=images
```

**Note**: In production mode, images are stored in Supabase Storage. In development, they're stored locally in the `uploads/` folder.

4. Run the application:
```bash
python main.py
```

The app will start in the mode specified in `.env`:
- **Development**: Debug mode enabled, auto-reload on code changes
- **Production**: Debug mode disabled, optimized for deployment

## API Documentation

Interactive API documentation is available at:
- **Swagger UI**: http://localhost:5000/docs

The Swagger UI provides:
- Complete API endpoint documentation
- Request/response schemas
- Interactive testing interface
- Authentication support

## Transform Parameters
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
- `optimize` - Enable both enhancement and compression (true/false)
- `enhance` - Enhance image quality only - sharpness, contrast, color (true/false)
- `compress` - Reduce file size only - size-based compression (true/false)
- `grayscale` - Convert to grayscale (true/false)
- `download` - Force download instead of display (true/false)

### Thumbnail Parameters
- `size` - Thumbnail size (e.g., 150x150, 200x200)
- `download` - Force download instead of display (true/false)

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

# Generate API Key (use token from login)
curl -X POST http://localhost:5000/api/auth/api-keys \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Production Server"}'

# List API Keys
curl http://localhost:5000/api/auth/api-keys \
  -H "Authorization: Bearer <token>"

# Upload with API Key (no JWT needed!)
curl -X POST http://localhost:5000/api/images/upload \
  -H "X-API-Key: sk_live_abc123..." \
  -F "file=@image.jpg"

# Upload with JWT (traditional way)
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

# Remove background
curl "http://localhost:5000/api/images/1/remove-background?format=png&download=true" \
  -H "Authorization: Bearer <token>" \
  --output no_background.png

# Batch upload multiple images
curl -X POST http://localhost:5000/api/batch/upload \
  -H "Authorization: Bearer <token>" \
  -F "files=@image1.jpg" \
  -F "files=@image2.jpg" \
  -F "files=@image3.jpg"

# Batch transform (returns ZIP)
curl -X POST http://localhost:5000/api/batch/transform \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"image_ids": [1, 2, 3], "width": 300, "format": "webp"}' \
  --output transformed.zip

# Batch remove background (returns ZIP)
curl -X POST http://localhost:5000/api/batch/remove-background \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"image_ids": [1, 2, 3], "format": "png"}' \
  --output no_backgrounds.zip
```

---

## Project Reference

This project is modeled after the [Image Processing Service](https://roadmap.sh/projects/image-processing-service) project from [roadmap.sh](https://roadmap.sh).
