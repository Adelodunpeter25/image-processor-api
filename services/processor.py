"""Image processing service for transformations and manipulations."""
from PIL import Image, ImageDraw, ImageFont
import io

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
                       optimize=False, rotate=None, watermark_text=None, grayscale=False):
        """
        Apply transformations to an image.
        
        Args:
            filepath: Path to the original image
            width: Target width for resize
            height: Target height for resize
            format: Output format (jpeg, png, webp)
            quality: Image quality (1-100)
            crop_x: Crop starting X coordinate
            crop_y: Crop starting Y coordinate
            crop_width: Crop width
            crop_height: Crop height
            optimize: Enable optimization
            rotate: Rotation angle in degrees
            watermark_text: Text to add as watermark
            grayscale: Convert to grayscale
            
        Returns:
            tuple: (BytesIO buffer, output_format)
        """
        with Image.open(filepath) as img:
            # Convert to RGB if necessary for certain operations
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            
            # Apply grayscale filter
            if grayscale:
                img = img.convert('L').convert('RGB')
            
            # Apply rotation
            if rotate is not None:
                img = img.rotate(rotate, expand=True)
            
            # Apply crop
            if crop_x is not None and crop_y is not None and crop_width and crop_height:
                img = img.crop((crop_x, crop_y, crop_x + crop_width, crop_y + crop_height))
            
            # Apply resize
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
            
            # Apply watermark
            if watermark_text:
                draw = ImageDraw.Draw(img)
                img_width, img_height = img.size
                font_size = max(20, img_width // 20)
                try:
                    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
                except:
                    font = ImageFont.load_default()
                
                bbox = draw.textbbox((0, 0), watermark_text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                # Position at bottom-right
                x = img_width - text_width - 10
                y = img_height - text_height - 10
                
                draw.text((x, y), watermark_text, fill=(255, 255, 255, 128), font=font)
            
            # Save to buffer
            output_format = format.upper() if format else img.format
            buffer = io.BytesIO()
            
            if optimize:
                img.save(buffer, format=output_format, quality=quality, optimize=True)
            else:
                img.save(buffer, format=output_format, quality=quality)
            
            buffer.seek(0)
            return buffer, output_format.lower()
    
    @staticmethod
    def generate_thumbnail(filepath, size=(150, 150)):
        """
        Generate thumbnail from image.
        
        Args:
            filepath: Path to the original image
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
