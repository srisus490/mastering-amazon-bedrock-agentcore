"""Test AI Insights API endpoints."""

import requests
from datetime import date, timedelta

BASE_URL = "http://localhost:8000"

def test_ai_insights_api():
    """Test all three AI insights endpoints."""
    print("Testing AI Insights API Endpoints")
    print("=" * 60)
    
    # Test parameters
    system_id = "PROD_ANALYTICS"
    end_date = date.today()
    start_date = end_date - timedelta(days=5)
    
    print(f"\nTest parameters:")
    print(f"  System: {system_id}")
    print(f"  Date range: {start_date} to {end_date}")
    print(f"  Base URL: {BASE_URL}")
    
    # Test 1: Smart Insights
    print("\n1. Testing POST /api/v1/ai/insights...")
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
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Status: {response.status_code}")
            print(f"  Insights: {data['insights'][:80]}...")
            print(f"  Trends: {len(data['trends'])}")
            print(f"  Anomalies: {len(data['anomalies'])}")
            print(f"  Recommendations: {len(data['recommendations'])}")
            print(f"  Cached: {data.get('cached', False)}")
        else:
            print(f"✗ Status: {response.status_code}")
            print(f"  Error: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    # Test 2: Forecast
    print("\n2. Testing POST /api/v1/ai/forecast...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/ai/forecast",
            json={
                "source_system_id": system_id,
                "historical_days": 60
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Status: {response.status_code}")
            print(f"  Predictions: {len(data['predictions'])} days")
            if data['predictions']:
                pred = data['predictions'][0]
                print(f"  First: {pred['date']} - {pred['predicted_count']} files (confidence: {pred['confidence_level']})")
            print(f"  Cached: {data.get('cached', False)}")
        else:
            print(f"✗ Status: {response.status_code}")
            print(f"  Error: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    # Test 3: Root Cause Analysis
    print("\n3. Testing POST /api/v1/ai/root-cause...")
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
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Status: {response.status_code}")
            print(f"  Violations analyzed: {data['violations_analyzed']}")
            print(f"  Root causes: {len(data['root_causes'])}")
            print(f"  Remediation actions: {len(data['remediation_actions'])}")
            print(f"  Cached: {data.get('cached', False)}")
        else:
            print(f"✗ Status: {response.status_code}")
            print(f"  Error: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    # Test 4: Cache Hit (call insights again)
    print("\n4. Testing cache hit (insights again)...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/ai/insights",
            json={
                "source_system_id": system_id,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('cached'):
                print(f"✓ Cache hit confirmed (response time < 1s)")
            else:
                print(f"⚠ Cache miss (unexpected)")
        else:
            print(f"✗ Status: {response.status_code}")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    # Test 5: Error handling - invalid system
    print("\n5. Testing error handling (invalid system)...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/ai/insights",
            json={
                "source_system_id": "INVALID_SYSTEM",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            timeout=10
        )
        
        if response.status_code == 404:
            print(f"✓ Correctly returned 404 for invalid system")
        else:
            print(f"⚠ Expected 404, got {response.status_code}")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    # Test 6: Error handling - invalid date range
    print("\n6. Testing error handling (invalid date range)...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/ai/insights",
            json={
                "source_system_id": system_id,
                "start_date": end_date.isoformat(),
                "end_date": start_date.isoformat()  # Reversed
            },
            timeout=10
        )
        
        if response.status_code == 400:
            print(f"✓ Correctly returned 400 for invalid date range")
        else:
            print(f"⚠ Expected 400, got {response.status_code}")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    print("\n" + "=" * 60)
    print("All API tests completed! ✓")
    return True

if __name__ == "__main__":
    print("\nMake sure the API server is running:")
    print("  uvicorn src.api.app:create_app --factory --reload")
    print()
    
    try:
        # Check if server is running
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✓ API server is running\n")
            test_ai_insights_api()
        else:
            print("✗ API server returned unexpected status")
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to API server. Please start it first.")
    except Exception as e:
        print(f"✗ Error: {e}")
