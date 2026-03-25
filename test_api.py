"""Test API endpoints"""

import requests

BASE_URL = "http://localhost:8000"

def test_endpoints():
    """Test various API endpoints"""
    
    print("Testing API endpoints...")
    print("=" * 50)
    
    # Test health
    print("\n1. Health check:")
    response = requests.get(f"{BASE_URL}/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    # Test root
    print("\n2. Root endpoint:")
    response = requests.get(f"{BASE_URL}/")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    # Test source systems
    print("\n3. Source systems:")
    response = requests.get(f"{BASE_URL}/api/v1/source-systems")
    print(f"   Status: {response.status_code}")
    print(f"   Count: {len(response.json())}")
    if response.json():
        print(f"   First system: {response.json()[0]}")
    
    # Test file arrivals count
    print("\n4. File arrivals count:")
    response = requests.get(f"{BASE_URL}/api/v1/file-arrivals/count")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    # Test trends summary
    print("\n5. Trends summary:")
    response = requests.get(f"{BASE_URL}/api/v1/trends/summary")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   Systems: {len(response.json())}")
    else:
        print(f"   Error: {response.json()}")
    
    print("\n" + "=" * 50)
    print("API tests completed!")

if __name__ == "__main__":
    try:
        test_endpoints()
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to API. Make sure it's running on port 8000")
    except Exception as e:
        print(f"ERROR: {e}")
