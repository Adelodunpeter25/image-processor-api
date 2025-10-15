"""Test batch processing functionality."""
import os
import sys
from io import BytesIO
from PIL import Image
import zipfile

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.processor import ImageProcessor

def create_test_images(count=3):
    """Create multiple test images."""
    images = []
    colors = ['red', 'green', 'blue', 'yellow', 'purple']
    
    for i in range(count):
        img = Image.new('RGB', (200, 200), color=colors[i % len(colors)])
        buffer = BytesIO()
        img.save(buffer, format='JPEG')
        buffer.seek(0)
        images.append(buffer)
    
    return images

def test_batch_transform():
    """Test transforming multiple images."""
    print("Testing Batch Transform...")
    
    try:
        # Create test images
        test_images = create_test_images(3)
        
        # Transform each image
        results = []
        for i, test_image in enumerate(test_images):
            print(f"  Transforming image {i+1}...")
            buffer, output_format = ImageProcessor.transform_image(
                test_image,
                width=100,
                height=100,
                format='png',
                quality=85
            )
            results.append((buffer, output_format))
        
        print(f"✅ Transformed {len(results)} images")
        
        # Verify all transformations
        for i, (buffer, output_format) in enumerate(results):
            assert output_format == 'png', f"Image {i+1}: Expected PNG format"
            assert len(buffer.getvalue()) > 0, f"Image {i+1}: Empty buffer"
            
            # Verify dimensions
            buffer.seek(0)
            img = Image.open(buffer)
            assert img.size == (100, 100), f"Image {i+1}: Wrong dimensions {img.size}"
            print(f"  Image {i+1}: {img.size}, {len(buffer.getvalue())} bytes")
        
        print("✅ Batch transform test passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        raise

def test_batch_zip_creation():
    """Test creating ZIP file with multiple processed images."""
    print("\nTesting ZIP Creation...")
    
    try:
        # Create test images
        test_images = create_test_images(5)
        
        # Create ZIP in memory
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for i, test_image in enumerate(test_images):
                # Transform image
                buffer, output_format = ImageProcessor.transform_image(
                    test_image,
                    width=50,
                    height=50,
                    grayscale=True
                )
                
                # Add to ZIP
                filename = f"image_{i+1}.{output_format}"
                zip_file.writestr(filename, buffer.getvalue())
        
        zip_buffer.seek(0)
        
        print(f"✅ Created ZIP file: {len(zip_buffer.getvalue())} bytes")
        
        # Verify ZIP contents
        with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
            file_list = zip_file.namelist()
            print(f"  Files in ZIP: {len(file_list)}")
            
            assert len(file_list) == 5, "Expected 5 files in ZIP"
            
            for filename in file_list:
                file_data = zip_file.read(filename)
                assert len(file_data) > 0, f"{filename}: Empty file"
                
                # Verify it's a valid image
                img = Image.open(BytesIO(file_data))
                assert img.size == (50, 50), f"{filename}: Wrong dimensions"
                print(f"  ✓ {filename}: {img.size}, {len(file_data)} bytes")
        
        print("✅ ZIP creation test passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        raise

if __name__ == '__main__':
    test_batch_transform()
    test_batch_zip_creation()
    print("\n" + "="*60)
    print("All batch processing tests passed! ✅")
    print("="*60)
