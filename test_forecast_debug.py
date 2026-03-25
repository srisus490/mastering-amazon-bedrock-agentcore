"""Debug forecast endpoint."""

import requests
from datetime import date, timedelta

BASE_URL = "http://localhost:8000"
system_id = "PROD_ANALYTICS"

print("Testing Forecast Endpoint")
print("=" * 60)

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
    print(f"Response: {response.text[:500]}")
    
    if response.status_code == 200:
        data = response.json()
        print("\nSuccess!")
        print(f"Predictions: {len(data.get('predictions', []))}")
    else:
        print("\nError!")
        
except Exception as e:
    print(f"Exception: {e}")
    import traceback
    traceback.print_exc()
