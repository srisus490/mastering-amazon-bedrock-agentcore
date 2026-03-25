"""Check if AI Insights endpoints are available."""

import requests
import json

BASE_URL = "http://localhost:8000"

print("Checking AI Insights API Endpoints")
print("=" * 60)

try:
    # Get OpenAPI spec
    response = requests.get(f"{BASE_URL}/openapi.json", timeout=5)
    
    if response.status_code == 200:
        spec = response.json()
        paths = spec.get("paths", {})
        
        # Check for our new endpoints
        ai_endpoints = [
            "/api/v1/ai/insights",
            "/api/v1/ai/forecast",
            "/api/v1/ai/root-cause"
        ]
        
        print("\nChecking for AI Insights endpoints:")
        for endpoint in ai_endpoints:
            if endpoint in paths:
                print(f"  ✓ {endpoint} - FOUND")
            else:
                print(f"  ✗ {endpoint} - NOT FOUND")
        
        print("\nAll available /api/v1/ai/* endpoints:")
        for path in sorted(paths.keys()):
            if path.startswith("/api/v1/ai"):
                methods = list(paths[path].keys())
                print(f"  - {path} [{', '.join(methods).upper()}]")
        
        # Check if endpoints are missing
        missing = [ep for ep in ai_endpoints if ep not in paths]
        if missing:
            print("\n" + "=" * 60)
            print("⚠ AI Insights endpoints are NOT loaded!")
            print("\nPlease restart the API server:")
            print("  1. Stop the server (Ctrl+C)")
            print("  2. Run: uvicorn src.api.app:create_app --factory --reload")
            print("  3. Wait for 'Application startup complete'")
            print("  4. Run this script again")
        else:
            print("\n" + "=" * 60)
            print("✓ All AI Insights endpoints are loaded!")
            print("\nYou can now run: python test_ai_api.py")
    else:
        print(f"✗ Failed to get OpenAPI spec: {response.status_code}")
        
except requests.exceptions.ConnectionError:
    print("✗ Cannot connect to API server")
    print("\nPlease start the server:")
    print("  uvicorn src.api.app:create_app --factory --reload")
except Exception as e:
    print(f"✗ Error: {e}")
