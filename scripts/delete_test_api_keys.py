"""Delete API keys for test user via API."""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv('PRODUCTION_URL', 'https://image-processor-api.vercel.app')
API_URL = f"{BASE_URL}/api"

TEST_EMAIL = "test_prod@example.com"
TEST_PASSWORD = "testpass123"

# Login
print("Logging in...")
response = requests.post(f"{API_URL}/auth/login", json={
    "email": TEST_EMAIL,
    "password": TEST_PASSWORD
})

if response.status_code != 200:
    print(f"❌ Login failed: {response.text}")
    exit(1)

token = response.json()['access_token']
print("✅ Logged in")

# List API keys
print("\nFetching API keys...")
response = requests.get(
    f"{API_URL}/auth/api-keys",
    headers={"Authorization": f"Bearer {token}"}
)

if response.status_code != 200:
    print(f"❌ Failed to list API keys: {response.text}")
    exit(1)

api_keys = response.json()['keys']
print(f"Found {len(api_keys)} API keys")

# Delete each API key
for key in api_keys:
    print(f"\nDeleting API key: {key['name']} (ID: {key['id']})")
    response = requests.delete(
        f"{API_URL}/auth/api-keys/{key['id']}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        print("  ✅ Deleted")
    else:
        print(f"  ❌ Failed: {response.text}")

print(f"\n✅ Deleted {len(api_keys)} API keys")
