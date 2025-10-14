"""Test thumbnail generation functionality."""
import os
import sys
from io import BytesIO
from PIL import Image

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.processor import ImageProcessor

def create_test_image(width=800, height=600):
    """Create a test image with specified dimensions."""
    img = Image.new('RGB', (width, height), color='blue')
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    # Draw some shapes
    draw.rectangle([100, 100, 300, 300], fill='yellow')
    draw.ellipse([400, 200, 600, 400], fill='green')
    
    buffer = BytesIO()
    img.save(buffer, format='JPEG')
    buffer.seek(0)
    return buffer

def test_thumbnail_generation():
    """Test generating thumbnails of different sizes."""
    print("Testing Thumbnail Generation...")
    
    test_sizes = [
        (150, 150),
        (200, 200),
        (100, 100),
        (300, 300)
    ]
    
    try:
        for size in test_sizes:
            print(f"\nTesting size: {size[0]}x{size[1]}")
            
            # Create test image
            test_image = create_test_image(800, 600)
            
            # Generate thumbnail
            result_buffer, output_format = ImageProcessor.generate_thumbnail(test_image, size)
            
            print("   ✅ Thumbnail generated")
            print(f"   Output format: {output_format}")
            print(f"   Result size: {len(result_buffer.getvalue())} bytes")
            
            # Verify output
            assert output_format in ['jpeg', 'jpg'], "Expected JPEG format"
            assert len(result_buffer.getvalue()) > 0, "Result buffer is empty"
            
            # Verify dimensions
            result_buffer.seek(0)
            result_img = Image.open(result_buffer)
            print(f"   Thumbnail dimensions: {result_img.size}")
            
            # Check that thumbnail fits within requested size
            assert result_img.size[0] <= size[0], f"Width exceeds {size[0]}"
            assert result_img.size[1] <= size[1], f"Height exceeds {size[1]}"
            
        print("\n✅ All thumbnail tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        raise

if __name__ == '__main__':
    test_thumbnail_generation()
