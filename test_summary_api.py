"""Test script for system summary API with date range"""

import requests
from datetime import date, timedelta

BASE_URL = "http://localhost:8000"

def test_summary_endpoints():
    """Test the summary endpoint with and without date range"""
    
    print("Testing System Summary API Endpoints")
    print("=" * 60)
    
    # Test 1: Summary without date range (today only)
    print("\n1. Summary without date range (today only):")
    url = f"{BASE_URL}/api/v1/trends/summary"
    print(f"URL: {url}")
    
    try:
        response = requests.get(url)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Systems returned: {len(data)}")
            if data:
                print(f"Sample system: {data[0]}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Summary with date range (last 5 days)
    print("\n2. Summary with date range (last 5 days):")
    end_date = date.today()
    start_date = end_date - timedelta(days=4)
    
    url = f"{BASE_URL}/api/v1/trends/summary?start_date={start_date}&end_date={end_date}"
    print(f"URL: {url}")
    print(f"Date range: {start_date} to {end_date}")
    
    try:
        response = requests.get(url)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Systems returned: {len(data)}")
            if data:
                print(f"Sample system: {data[0]}")
                # Show file counts for first few systems
                print("\nFile counts by system:")
                for system in data[:5]:
                    print(f"  - {system['source_system_id']}: {system['file_count']} files")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Summary with specific date
    print("\n3. Summary with specific target_date:")
    target_date = date.today() - timedelta(days=2)
    
    url = f"{BASE_URL}/api/v1/trends/summary?target_date={target_date}"
    print(f"URL: {url}")
    print(f"Target date: {target_date}")
    
    try:
        response = requests.get(url)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Systems returned: {len(data)}")
            if data:
                print(f"Sample system: {data[0]}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_summary_endpoints()
