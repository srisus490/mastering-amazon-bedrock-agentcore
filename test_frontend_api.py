"""Test what the frontend is actually calling."""

import requests
from datetime import date, timedelta

BASE_URL = "http://localhost:8000"

# Use the same system and dates as shown in the screenshot
system_id = "PROD_ARCHIVE"
end_date = date(2026, 4, 19)
start_date = date(2026, 2, 10)

print("Testing Frontend API Calls")
print("=" * 60)
print(f"System: {system_id}")
print(f"Date range: {start_date} to {end_date}")
print()

# Test 1: Smart Insights
print("1. Testing Smart Insights...")
try:
    response = requests.post(
        f"{BASE_URL}/api/v1/ai/insights",
        json={
            "source_system_id": system_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        },
        timeout=60
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Success")
        print(f"  Insights: {data['insights'][:100]}...")
        print(f"  Cached: {data.get('cached', False)}")
    else:
        print(f"✗ Error: {response.text}")
except Exception as e:
    print(f"✗ Exception: {e}")

print()

# Test 2: Forecast
print("2. Testing Forecast...")
try:
    response = requests.post(
        f"{BASE_URL}/api/v1/ai/forecast",
        json={
            "source_system_id": system_id,
            "historical_days": 60
        },
        timeout=60
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Success")
        print(f"  Predictions: {len(data['predictions'])}")
        print(f"  Cached: {data.get('cached', False)}")
    else:
        print(f"✗ Error: {response.text}")
except Exception as e:
    print(f"✗ Exception: {e}")

print()

# Test 3: Root Cause
print("3. Testing Root Cause...")
try:
    response = requests.post(
        f"{BASE_URL}/api/v1/ai/root-cause",
        json={
            "source_system_id": system_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        },
        timeout=60
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Success")
        print(f"  Violations: {data['violations_analyzed']}")
        print(f"  Cached: {data.get('cached', False)}")
    else:
        print(f"✗ Error: {response.text}")
except Exception as e:
    print(f"✗ Exception: {e}")
