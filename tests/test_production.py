"""Production integration tests - tests all operations with Supabase."""
import requests
import os
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

# Production API URL
BASE_URL = os.getenv('PRODUCTION_URL', 'http://localhost:5000')
API_URL = f"{BASE_URL}/api"

# Test credentials
TEST_EMAIL = "test_prod@example.com"
TEST_PASSWORD = "testpass123"

# Global token storage
token = None
api_key = None
test_image_id = None

def create_test_image():
    """Create a test image in memory."""
    img = Image.new('RGB', (800, 600), color='blue')
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer

def test_1_register():
    """Test user registration."""
    print("\n1. Testing Registration...")
    
    response = requests.post(f"{API_URL}/auth/register", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    
    if response.status_code == 201:
        print("✅ Registration successful")
    elif response.status_code == 400 and "already" in response.text.lower():
        print("✅ User already exists (OK)")
    else:
        print(f"❌ Registration failed: {response.status_code} - {response.text}")

def test_2_login():
    """Test user login."""
    global token
    print("\n2. Testing Login...")
    
    response = requests.post(f"{API_URL}/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    token = data['access_token']
    print(f"✅ Login successful - Token: {token[:20]}...")

def test_3_generate_api_key():
    """Test API key generation."""
    global api_key
    print("\n3. Testing API Key Generation...")
    
    response = requests.post(
        f"{API_URL}/auth/api-keys",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Production Test Key"}
    )
    
    assert response.status_code == 201, f"API key generation failed: {response.text}"
    data = response.json()
    api_key = data['api_key']
    print(f"✅ API key generated: {api_key[:20]}...")

def test_4_upload_with_jwt():
    """Test image upload with JWT token."""
    global test_image_id
    print("\n4. Testing Upload with JWT...")
    
    test_image = create_test_image()
    
    response = requests.post(
        f"{API_URL}/images/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("test.png", test_image, "image/png")}
    )
    
    assert response.status_code == 201, f"Upload failed: {response.text}"
    data = response.json()
    test_image_id = data['image_id']
    print(f"✅ Upload successful - Image ID: {test_image_id}")
    print(f"   Format: {data['format']}, Size: {data['width']}x{data['height']}")

def test_5_upload_with_api_key():
    """Test image upload with API key."""
    print("\n5. Testing Upload with API Key...")
    
    test_image = create_test_image()
    
    response = requests.post(
        f"{API_URL}/images/upload",
        headers={"X-API-Key": api_key},
        files={"file": ("test2.png", test_image, "image/png")}
    )
    
    assert response.status_code == 201, f"Upload with API key failed: {response.text}"
    data = response.json()
    print(f"✅ Upload with API key successful - Image ID: {data['image_id']}")

def test_6_list_images():
    """Test listing images."""
    print("\n6. Testing List Images...")
    
    response = requests.get(
        f"{API_URL}/images",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200, f"List images failed: {response.text}"
    data = response.json()
    print(f"✅ Listed {len(data['images'])} images")

def test_7_transform_resize():
    """Test image transformation - resize."""
    print("\n7. Testing Transform (Resize)...")
    
    response = requests.get(
        f"{API_URL}/images/{test_image_id}/transform?width=400&height=300",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200, f"Transform failed: {response.text}"
    assert response.headers['Content-Type'].startswith('image/'), "Not an image response"
    print(f"✅ Transform successful - Size: {len(response.content)} bytes")

def test_8_transform_format():
    """Test image transformation - format conversion."""
    print("\n8. Testing Transform (Format Conversion)...")
    
    response = requests.get(
        f"{API_URL}/images/{test_image_id}/transform?format=webp&quality=80",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200, f"Format conversion failed: {response.text}"
    print(f"✅ Format conversion successful - Size: {len(response.content)} bytes")

def test_9_transform_rotate():
    """Test image transformation - rotate."""
    print("\n9. Testing Transform (Rotate)...")
    
    response = requests.get(
        f"{API_URL}/images/{test_image_id}/transform?rotate=90",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200, f"Rotate failed: {response.text}"
    print("✅ Rotate successful")

def test_10_transform_watermark():
    """Test image transformation - watermark."""
    print("\n10. Testing Transform (Watermark)...")
    
    response = requests.get(
        f"{API_URL}/images/{test_image_id}/transform?watermark=Test%20Watermark",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200, f"Watermark failed: {response.text}"
    print("✅ Watermark successful")

def test_11_thumbnail():
    """Test thumbnail generation."""
    print("\n11. Testing Thumbnail Generation...")
    
    response = requests.get(
        f"{API_URL}/images/{test_image_id}/thumbnail?size=200x200",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200, f"Thumbnail failed: {response.text}"
    print(f"✅ Thumbnail successful - Size: {len(response.content)} bytes")

def test_12_batch_upload():
    """Test batch upload."""
    print("\n12. Testing Batch Upload...")
    
    files = [
        ("files", ("batch1.png", create_test_image(), "image/png")),
        ("files", ("batch2.png", create_test_image(), "image/png")),
        ("files", ("batch3.png", create_test_image(), "image/png"))
    ]
    
    response = requests.post(
        f"{API_URL}/batch/upload",
        headers={"Authorization": f"Bearer {token}"},
        files=files
    )
    
    assert response.status_code == 201, f"Batch upload failed: {response.text}"
    data = response.json()
    print(f"✅ Batch upload successful - {len(data['images'])} images")

def test_13_list_presets():
    """Test listing presets."""
    print("\n13. Testing List Presets...")
    
    response = requests.get(
        f"{API_URL}/presets",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200, f"List presets failed: {response.text}"
    data = response.json()
    print(f"✅ Listed {len(data['presets'])} presets")

def test_14_create_preset():
    """Test creating a preset."""
    print("\n14. Testing Create Preset...")
    
    import time
    unique_name = f"Test Preset {int(time.time())}"
    
    response = requests.post(
        f"{API_URL}/presets",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": unique_name,
            "description": "Test preset for production",
            "width": 500,
            "height": 500,
            "format": "jpeg",
            "quality": 85
        }
    )
    
    assert response.status_code == 201, f"Create preset failed: {response.text}"
    data = response.json()
    print(f"✅ Preset created - ID: {data['preset']['id']}")

def test_15_rate_limiting():
    """Test rate limiting."""
    print("\n15. Testing Rate Limiting...")
    
    # Make requests until rate limited
    success_count = 0
    rate_limited = False
    
    for i in range(200):  # Try up to 200 requests
        response = requests.get(
            f"{API_URL}/images",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 200:
            success_count += 1
        elif response.status_code == 429:
            rate_limited = True
            print(f"✅ Rate limiting working - Limited after {success_count} successful requests")
            break
    
    if not rate_limited:
        print(f"⚠️  Rate limiting not triggered after {success_count} requests")
    
    assert rate_limited, "Rate limiting should have been triggered"

def test_16_health_check():
    """Test health check endpoint."""
    print("\n16. Testing Health Check...")
    
    response = requests.get(f"{BASE_URL}/health")
    
    assert response.status_code == 200, f"Health check failed: {response.text}"
    data = response.json()
    print(f"✅ Health check passed - Status: {data['status']}")

def test_17_delete_image():
    """Test image deletion."""
    print("\n17. Testing Delete Image...")
    
    response = requests.delete(
        f"{API_URL}/images/{test_image_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200, f"Delete failed: {response.text}"
    print("✅ Image deleted successfully")

if __name__ == '__main__':
    print("="*60)
    print("PRODUCTION INTEGRATION TESTS")
    print(f"Testing against: {BASE_URL}")
    print("="*60)
    
    try:
        test_1_register()
        test_2_login()
        test_3_generate_api_key()
        test_4_upload_with_jwt()
        test_5_upload_with_api_key()
        test_6_list_images()
        test_7_transform_resize()
        test_8_transform_format()
        test_9_transform_rotate()
        test_10_transform_watermark()
        test_11_thumbnail()
        test_12_batch_upload()
        test_13_list_presets()
        test_14_create_preset()
        test_15_rate_limiting()
        test_16_health_check()
        test_17_delete_image()
        
        print("\n" + "="*60)
        print("✅ ALL PRODUCTION TESTS PASSED!")
        print("="*60)
        
    except Exception as e:
        print("\n" + "="*60)
        print(f"❌ TEST FAILED: {str(e)}")
        print("="*60)
        raise
