"""Test trends API endpoints"""

import requests
import urllib.parse

BASE_URL = "http://localhost:8000"

def test_trends():
    """Test trends endpoints for a specific system"""
    
    # Test with PROD_ANALYTICS since we know it has 11 files
    system_id = "PROD_ANALYTICS"
    print(f"Testing with system: {system_id}")
    print("=" * 60)
    
    # Test daily trends
    print("\n1. Daily trends (30 days):")
    url = f"{BASE_URL}/api/v1/trends/daily/{urllib.parse.quote(system_id)}?days=30"
    print(f"   URL: {url}")
    try:
        response = requests.get(url)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Data points: {len(data)}")
            if data:
                print(f"   Sample: {data[0]}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test moving average
    print("\n2. Moving average (30 days):")
    url = f"{BASE_URL}/api/v1/trends/moving-average/{urllib.parse.quote(system_id)}?days=30"
    print(f"   URL: {url}")
    try:
        response = requests.get(url)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Data points: {len(data)}")
            if data:
                print(f"   Sample: {data[0]}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test hourly patterns
    print("\n3. Hourly patterns (30 days):")
    url = f"{BASE_URL}/api/v1/trends/hourly-patterns/{urllib.parse.quote(system_id)}?days=30"
    print(f"   URL: {url}")
    try:
        response = requests.get(url)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Data points: {len(data)}")
            if data:
                print(f"   Sample: {data[0]}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    try:
        test_trends()
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to API. Make sure it's running on port 8000")
        print("Run: uvicorn src.api.app:create_app --factory --reload")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
