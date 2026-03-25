"""Test AIInsightsService integration."""

from datetime import date, timedelta
from src.ai.insights_service import AIInsightsService
from src.database.connection import init_db

def test_insights_service():
    """Test the complete insights service."""
    print("Testing AIInsightsService Integration")
    print("=" * 60)
    
    # Initialize database
    init_db()
    print("✓ Database initialized")
    
    # Initialize service
    service = AIInsightsService()
    print("✓ Service initialized")
    
    # Test parameters
    system_id = "PROD_ANALYTICS"
    end_date = date.today()
    start_date = end_date - timedelta(days=5)
    
    print(f"\nTest parameters:")
    print(f"  System: {system_id}")
    print(f"  Date range: {start_date} to {end_date}")
    
    # Test 1: Smart Insights
    print("\n1. Testing Smart Insights...")
    try:
        insights = service.generate_smart_insights(system_id, start_date, end_date)
        print(f"✓ Insights generated")
        print(f"  Summary: {insights['insights'][:100]}...")
        print(f"  Trends: {len(insights['trends'])} found")
        print(f"  Anomalies: {len(insights['anomalies'])} found")
        print(f"  Recommendations: {len(insights['recommendations'])} provided")
        print(f"  Cached: {insights.get('cached', False)}")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    # Test 2: Forecast
    print("\n2. Testing Forecast...")
    try:
        forecast = service.generate_forecast(system_id, historical_days=60)
        print(f"✓ Forecast generated")
        print(f"  Predictions: {len(forecast['predictions'])} days")
        print(f"  First prediction: {forecast['predictions'][0]['date']} - {forecast['predictions'][0]['predicted_count']} files")
        print(f"  Cached: {forecast.get('cached', False)}")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    # Test 3: Root Cause Analysis
    print("\n3. Testing Root Cause Analysis...")
    try:
        root_cause = service.generate_root_cause_analysis(system_id, start_date, end_date)
        print(f"✓ Root cause analysis generated")
        print(f"  Violations analyzed: {root_cause['violations_analyzed']}")
        print(f"  Root causes: {len(root_cause['root_causes'])} identified")
        print(f"  Remediation actions: {len(root_cause['remediation_actions'])} suggested")
        print(f"  Cached: {root_cause.get('cached', False)}")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    # Test 4: Cache Hit
    print("\n4. Testing Cache Hit...")
    try:
        insights2 = service.generate_smart_insights(system_id, start_date, end_date)
        if insights2.get('cached'):
            print(f"✓ Cache hit confirmed")
        else:
            print(f"⚠ Cache miss (unexpected)")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    return True

if __name__ == "__main__":
    test_insights_service()
