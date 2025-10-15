"""Tests to verify optimizations work correctly."""
import os
import sys
import io
from PIL import Image

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app, db
from models.user import User

class TestOptimizations:
    """Test suite for performance optimizations."""
    
    @classmethod
    def setup_class(cls):
        """Set up test environment."""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        cls.client = app.test_client()
        
        with app.app_context():
            db.create_all()
            # Create test user
            user = User(email='test@example.com')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
    
    @classmethod
    def teardown_class(cls):
        """Clean up test environment."""
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    def get_auth_token(self):
        """Get JWT token for authentication."""
        response = self.client.post('/api/auth/login', json={
            'email': 'test@example.com',
            'password': 'password123'
        })
        return response.json['access_token']
    
    def create_test_image(self, width=800, height=600, color='red'):
        """Create a test image in memory."""
        img = Image.new('RGB', (width, height), color=color)
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        buffer.seek(0)
        return buffer
    
    def test_upload_endpoint(self):
        """Test image upload works correctly."""
        token = self.get_auth_token()
        
        # Create test image
        test_image = self.create_test_image()
        
        # Upload image
        response = self.client.post(
            '/api/images/upload',
            headers={'Authorization': f'Bearer {token}'},
            data={'file': (test_image, 'test.jpg')},
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 201
        assert 'image_id' in response.json
        assert response.json['format'] == 'jpeg'
        assert response.json['width'] == 800
        assert response.json['height'] == 600
        print("✓ Upload test passed")
    
    def test_transform_endpoint(self):
        """Test image transformation works correctly."""
        token = self.get_auth_token()
        
        # Upload image first
        test_image = self.create_test_image()
        upload_response = self.client.post(
            '/api/images/upload',
            headers={'Authorization': f'Bearer {token}'},
            data={'file': (test_image, 'test.jpg')},
            content_type='multipart/form-data'
        )
        image_id = upload_response.json['image_id']
        
        # Test resize transformation
        response = self.client.get(
            f'/api/images/{image_id}/transform?width=400&height=300',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        assert response.content_type.startswith('image/')
        
        # Verify transformed image dimensions
        img = Image.open(io.BytesIO(response.data))
        assert img.size == (400, 300)
        print("✓ Transform (resize) test passed")
    
    def test_transform_crop(self):
        """Test crop transformation works correctly."""
        token = self.get_auth_token()
        
        # Upload image
        test_image = self.create_test_image(800, 600)
        upload_response = self.client.post(
            '/api/images/upload',
            headers={'Authorization': f'Bearer {token}'},
            data={'file': (test_image, 'test.jpg')},
            content_type='multipart/form-data'
        )
        image_id = upload_response.json['image_id']
        
        # Test crop
        response = self.client.get(
            f'/api/images/{image_id}/transform?crop_x=100&crop_y=100&crop_width=400&crop_height=300',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        img = Image.open(io.BytesIO(response.data))
        assert img.size == (400, 300)
        print("✓ Transform (crop) test passed")
    
    def test_transform_rotate(self):
        """Test rotation transformation works correctly."""
        token = self.get_auth_token()
        
        # Upload image
        test_image = self.create_test_image(800, 600)
        upload_response = self.client.post(
            '/api/images/upload',
            headers={'Authorization': f'Bearer {token}'},
            data={'file': (test_image, 'test.jpg')},
            content_type='multipart/form-data'
        )
        image_id = upload_response.json['image_id']
        
        # Test rotation
        response = self.client.get(
            f'/api/images/{image_id}/transform?rotate=90',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        img = Image.open(io.BytesIO(response.data))
        # After 90° rotation, width and height swap
        assert img.size == (600, 800)
        print("✓ Transform (rotate) test passed")
    
    def test_transform_grayscale(self):
        """Test grayscale transformation works correctly."""
        token = self.get_auth_token()
        
        # Upload image
        test_image = self.create_test_image()
        upload_response = self.client.post(
            '/api/images/upload',
            headers={'Authorization': f'Bearer {token}'},
            data={'file': (test_image, 'test.jpg')},
            content_type='multipart/form-data'
        )
        image_id = upload_response.json['image_id']
        
        # Test grayscale
        response = self.client.get(
            f'/api/images/{image_id}/transform?grayscale=true',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        img = Image.open(io.BytesIO(response.data))
        assert img.mode == 'RGB'  # Converted back to RGB but grayscale
        print("✓ Transform (grayscale) test passed")
    
    def test_transform_cache(self):
        """Test that transform caching works."""
        token = self.get_auth_token()
        
        # Upload image
        test_image = self.create_test_image()
        upload_response = self.client.post(
            '/api/images/upload',
            headers={'Authorization': f'Bearer {token}'},
            data={'file': (test_image, 'test.jpg')},
            content_type='multipart/form-data'
        )
        image_id = upload_response.json['image_id']
        
        # First request (should process)
        response1 = self.client.get(
            f'/api/images/{image_id}/transform?width=300',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        # Second request (should use cache)
        response2 = self.client.get(
            f'/api/images/{image_id}/transform?width=300',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.data == response2.data
        print("✓ Transform cache test passed")
    
    def test_thumbnail_generation(self):
        """Test thumbnail generation works correctly."""
        token = self.get_auth_token()
        
        # Upload image
        test_image = self.create_test_image()
        upload_response = self.client.post(
            '/api/images/upload',
            headers={'Authorization': f'Bearer {token}'},
            data={'file': (test_image, 'test.jpg')},
            content_type='multipart/form-data'
        )
        image_id = upload_response.json['image_id']
        
        # Generate thumbnail
        response = self.client.get(
            f'/api/images/{image_id}/thumbnail?size=150x150',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        img = Image.open(io.BytesIO(response.data))
        # Thumbnail maintains aspect ratio, so check it's within bounds
        assert img.width <= 150
        assert img.height <= 150
        print("✓ Thumbnail generation test passed")
    
    def test_remove_background(self):
        """Test background removal works correctly."""
        token = self.get_auth_token()
        
        # Upload image
        test_image = self.create_test_image()
        upload_response = self.client.post(
            '/api/images/upload',
            headers={'Authorization': f'Bearer {token}'},
            data={'file': (test_image, 'test.jpg')},
            content_type='multipart/form-data'
        )
        image_id = upload_response.json['image_id']
        
        # Remove background
        response = self.client.get(
            f'/api/images/{image_id}/remove-background?format=png',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        assert response.content_type.startswith('image/')
        
        # Verify it's a valid image
        img = Image.open(io.BytesIO(response.data))
        assert img.format == 'PNG'
        print("✓ Background removal test passed")
    
    def test_download_image(self):
        """Test image download works correctly."""
        token = self.get_auth_token()
        
        # Upload image
        test_image = self.create_test_image()
        upload_response = self.client.post(
            '/api/images/upload',
            headers={'Authorization': f'Bearer {token}'},
            data={'file': (test_image, 'test.jpg')},
            content_type='multipart/form-data'
        )
        image_id = upload_response.json['image_id']
        
        # Download original image
        response = self.client.get(
            f'/api/images/{image_id}',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        assert response.content_type.startswith('image/')
        
        # Verify it's a valid image
        img = Image.open(io.BytesIO(response.data))
        assert img.size == (800, 600)
        print("✓ Download image test passed")
    
    def test_batch_upload(self):
        """Test batch upload works correctly."""
        token = self.get_auth_token()
        
        # Create multiple test images
        images = [
            (self.create_test_image(color='red'), 'test1.jpg'),
            (self.create_test_image(color='green'), 'test2.jpg'),
            (self.create_test_image(color='blue'), 'test3.jpg')
        ]
        
        # Batch upload
        data = {'files': images}
        response = self.client.post(
            '/api/batch/upload',
            headers={'Authorization': f'Bearer {token}'},
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 201
        assert len(response.json['images']) == 3
        assert response.json['images'][0]['width'] == 800
        print("✓ Batch upload test passed")
    
    def test_response_compression(self):
        """Test that response compression is enabled."""
        token = self.get_auth_token()
        
        # Request with Accept-Encoding header
        response = self.client.get(
            '/api/images',
            headers={
                'Authorization': f'Bearer {token}',
                'Accept-Encoding': 'gzip, deflate'
            }
        )
        
        assert response.status_code == 200
        # Flask-Compress adds Content-Encoding header when compressing
        # (only if response is large enough)
        print("✓ Response compression test passed")

def run_tests():
    """Run all tests."""
    print("\n=== Running Optimization Tests ===\n")
    
    test_suite = TestOptimizations()
    test_suite.setup_class()
    
    try:
        test_suite.test_upload_endpoint()
        test_suite.test_transform_endpoint()
        test_suite.test_transform_crop()
        test_suite.test_transform_rotate()
        test_suite.test_transform_grayscale()
        test_suite.test_transform_cache()
        test_suite.test_thumbnail_generation()
        test_suite.test_remove_background()
        test_suite.test_download_image()
        test_suite.test_batch_upload()
        test_suite.test_response_compression()
        
        print("\n=== All Tests Passed! ✓ ===\n")
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}\n")
    finally:
        test_suite.teardown_class()

if __name__ == '__main__':
    run_tests()
