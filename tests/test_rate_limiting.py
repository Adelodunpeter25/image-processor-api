"""Test rate limiting in production."""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv('PRODUCTION_URL', 'https://image-processor-api.vercel.app')
API_URL = f"{BASE_URL}/api"

TEST_EMAIL = "test_prod@example.com"
TEST_PASSWORD = "testpass123"

def test_rate_limiting():
    """Test rate limiting by making requests until 429 is returned."""
    print("="*60)
    print("RATE LIMITING TEST")
    print(f"Testing against: {BASE_URL}")
    print("="*60)
    
    # Login
    print("\n1. Logging in...")
    response = requests.post(f"{API_URL}/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        return
    
    token = response.json()['access_token']
    print(f"✅ Logged in")
    
    # Make requests until rate limited
    print("\n2. Making requests until rate limited...")
    success_count = 0
    rate_limited = False
    
    for i in range(200):
        response = requests.get(
            f"{API_URL}/images",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            success_count += 1
            if (i + 1) % 10 == 0:
                print(f"   {success_count} successful requests...")
        elif response.status_code == 429:
            rate_limited = True
            print(f"\n✅ Rate limit triggered after {success_count} successful requests")
            print(f"   Response: {response.json()}")
            break
        else:
            print(f"\n⚠️  Unexpected status code: {response.status_code}")
            print(f"   Response: {response.text}")
            break
    
    if not rate_limited:
        print(f"\n⚠️  Rate limiting NOT triggered after {success_count} requests")
        print("   This might indicate rate limiting is not configured properly")
    
    print("\n" + "="*60)
    if rate_limited:
        print("✅ RATE LIMITING TEST PASSED")
    else:
        print("❌ RATE LIMITING TEST FAILED")
    print("="*60)

if __name__ == '__main__':
    test_rate_limiting()
