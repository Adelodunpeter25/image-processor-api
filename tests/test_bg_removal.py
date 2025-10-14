"""Test background removal functionality."""
import os
import sys
from io import BytesIO
from PIL import Image

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.processor import ImageProcessor

def create_test_image_with_subject():
    """Create a test image with a simple subject."""
    # Create image with red circle on white background
    img = Image.new('RGB', (200, 200), color='white')
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.ellipse([50, 50, 150, 150], fill='red')
    
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer

def test_background_removal():
    """Test removing background from image."""
    print("Testing Background Removal...")
    
    try:
        # Create test image
        test_image = create_test_image_with_subject()
        
        # Remove background
        print("Removing background...")
        result_buffer, output_format = ImageProcessor.remove_background(test_image, format='png')
        
        print("✅ Background removal successful!")
        print(f"   Output format: {output_format}")
        print(f"   Result size: {len(result_buffer.getvalue())} bytes")
        
        # Verify output
        assert output_format == 'png', "Expected PNG format"
        assert len(result_buffer.getvalue()) > 0, "Result buffer is empty"
        
        # Verify it's a valid image
        result_buffer.seek(0)
        result_img = Image.open(result_buffer)
        assert result_img.mode == 'RGBA', "Expected RGBA mode for transparency"
        
        print(f"   Image dimensions: {result_img.size}")
        print(f"   Image mode: {result_img.mode}")
        print("✅ Test passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        raise

if __name__ == '__main__':
    test_background_removal()
