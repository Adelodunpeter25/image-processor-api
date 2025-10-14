"""Test Supabase storage upload functionality."""
import os
import sys
from io import BytesIO
from PIL import Image

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.storage import StorageService

def create_test_image():
    """Create a test image in memory."""
    from werkzeug.datastructures import FileStorage
    
    img = Image.new('RGB', (100, 100), color='red')
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    # Create FileStorage object (mimics Flask file upload)
    file_storage = FileStorage(
        stream=buffer,
        filename='test_image.png',
        content_type='image/png'
    )
    
    return file_storage

def test_supabase_upload():
    """Test uploading image to Supabase storage."""
    print("Testing Supabase Upload...")
    
    # Set environment to production
    os.environ['FLASK_ENV'] = 'production'
    
    try:
        # Initialize storage service
        storage = StorageService('uploads')
        
        # Create test image
        test_image = create_test_image()
        
        # Upload to Supabase
        print("Uploading test image to Supabase...")
        filepath, filename = storage.save_file(test_image, user_id=999)
        
        print("✅ Upload successful!")
        print(f"   Filename: {filename}")
        print(f"   URL: {filepath}")
        
        # Verify it's a URL
        assert filepath.startswith('http'), "Expected Supabase URL"
        
        # Clean up - delete the test file
        print("Cleaning up...")
        storage.delete_file(filepath)
        print("✅ Test passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        raise
    finally:
        # Reset environment
        os.environ['FLASK_ENV'] = 'development'

if __name__ == '__main__':
    test_supabase_upload()
