"""Image processing service for transformations and manipulations."""
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import io
import hashlib
from functools import lru_cache

# In-memory cache for transformed images (max 100 items)
_transform_cache = {}
_cache_max_size = 100

def get_transform_cache_key(filepath, width, height, format, quality, 
                            crop_x, crop_y, crop_width, crop_height,
                            optimize, enhance, compress, rotate, watermark_text, grayscale):
    """Generate cache key for transformation parameters."""
    params = f"{filepath}_{width}_{height}_{format}_{quality}_{crop_x}_{crop_y}_{crop_width}_{crop_height}_{optimize}_{enhance}_{compress}_{rotate}_{watermark_text}_{grayscale}"
    return hashlib.md5(params.encode()).hexdigest()

def clear_transform_cache():
    """Clear the transformation cache."""
    global _transform_cache
    _transform_cache.clear()

class ImageProcessor:
    """Handles image processing operations like resize, crop, rotate, etc."""
    
    @staticmethod
    def get_image_info(filepath):
        """
        Extract metadata from image file.
        
        Args:
            filepath: Path to the image file
            
        Returns:
            dict: Image metadata (format, width, height, size)
        """
        with Image.open(filepath) as img:
            return {
                'format': img.format.lower(),
                'width': img.width,
                'height': img.height,
                'size': img.size
            }
    
    @staticmethod
    def transform_image(filepath, width=None, height=None, format=None, quality=85, 
                       crop_x=None, crop_y=None, crop_width=None, crop_height=None, 
                       optimize=False, enhance=False, compress=False, 
                       rotate=None, watermark_text=None, grayscale=False):
        """
        Apply transformations to an image.
        
        Args:
            filepath: Path to the original image or BytesIO object
            width: Target width for resize
            height: Target height for resize
            format: Output format (jpeg, png, webp)
            quality: Image quality (1-100)
            crop_x: Crop starting X coordinate
            crop_y: Crop starting Y coordinate
            crop_width: Crop width
            crop_height: Crop height
            optimize: Enable both enhancement and compression (legacy)
            enhance: Enhance image quality (sharpness, contrast, color)
            compress: Reduce file size aggressively
            rotate: Rotation angle in degrees
            watermark_text: Text to add as watermark
            grayscale: Convert to grayscale
            
        Returns:
            tuple: (BytesIO buffer, output_format)
        """
        global _transform_cache
        
        # Generate cache key
        cache_key = get_transform_cache_key(
            str(filepath), width, height, format, quality,
            crop_x, crop_y, crop_width, crop_height,
            optimize, enhance, compress, rotate, watermark_text, grayscale
        )
        
        # Check cache
        if cache_key in _transform_cache:
            cached_buffer, cached_format = _transform_cache[cache_key]
            # Return a copy of the cached buffer
            buffer_copy = io.BytesIO(cached_buffer.getvalue())
            return buffer_copy, cached_format
        
        # Process image with lazy loading
        with Image.open(filepath) as img:
            # Convert to RGB if necessary for certain operations
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            
            # OPTIMIZATION: Crop FIRST to reduce image size for subsequent operations
            if crop_x is not None and crop_y is not None and crop_width and crop_height:
                img = img.crop((crop_x, crop_y, crop_x + crop_width, crop_y + crop_height))
            
            # Apply resize (on smaller cropped image if crop was applied)
            if width or height:
                original_width, original_height = img.size
                if width and height:
                    img = img.resize((width, height))
                elif width:
                    height = int((width / original_width) * original_height)
                    img = img.resize((width, height))
                elif height:
                    width = int((height / original_height) * original_width)
                    img = img.resize((width, height))
            
            # Apply rotation
            if rotate is not None:
                img = img.rotate(rotate, expand=True)
            
            # Apply grayscale filter
            if grayscale:
                img = img.convert('L').convert('RGB')
            
            # Apply watermark
            if watermark_text:
                draw = ImageDraw.Draw(img)
                img_width, img_height = img.size
                font_size = max(20, img_width // 20)
                try:
                    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
                except (OSError, IOError):
                    font = ImageFont.load_default()
                
                bbox = draw.textbbox((0, 0), watermark_text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                # Position at bottom-right
                x = img_width - text_width - 10
                y = img_height - text_height - 10
                
                draw.text((x, y), watermark_text, fill=(255, 255, 255, 128), font=font)
            
            # Apply quality enhancements
            if optimize or enhance:
                # Enhance sharpness
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(1.2)
                
                # Enhance contrast slightly
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.1)
                
                # Enhance color
                enhancer = ImageEnhance.Color(img)
                img = enhancer.enhance(1.05)
            
            # Save to buffer
            output_format = format.upper() if format else (img.format if img.format else 'JPEG')
            buffer = io.BytesIO()
            
            # Apply compression
            if optimize or compress:
                # Aggressive compression with reduced quality for smaller files
                save_quality = quality if quality != 85 else 65
                
                if output_format in ['JPEG', 'JPG']:
                    img.save(buffer, format=output_format, quality=save_quality, optimize=True, 
                            progressive=True, subsampling='4:2:0')
                elif output_format == 'PNG':
                    img.save(buffer, format=output_format, optimize=True, compress_level=9)
                elif output_format == 'WEBP':
                    img.save(buffer, format=output_format, quality=save_quality, method=6, lossless=False)
                else:
                    img.save(buffer, format=output_format, quality=save_quality, optimize=True)
            else:
                img.save(buffer, format=output_format, quality=quality)
            
            buffer.seek(0)
            
            # Store in cache (with size limit)
            if len(_transform_cache) >= _cache_max_size:
                # Remove oldest entry (simple FIFO)
                _transform_cache.pop(next(iter(_transform_cache)))
            
            # Cache a copy of the buffer
            cache_buffer = io.BytesIO(buffer.getvalue())
            _transform_cache[cache_key] = (cache_buffer, output_format.lower())
            
            return buffer, output_format.lower()
    
    @staticmethod
    def generate_thumbnail(filepath, size=(150, 150)):
        """
        Generate thumbnail from image.
        
        Args:
            filepath: Path to the original image or BytesIO object
            size: Tuple of (width, height) for thumbnail
            
        Returns:
            tuple: (BytesIO buffer, output_format)
        """
        with Image.open(filepath) as img:
            img.thumbnail(size)
            buffer = io.BytesIO()
            img.save(buffer, format=img.format, quality=85)
            buffer.seek(0)
            return buffer, img.format.lower()
