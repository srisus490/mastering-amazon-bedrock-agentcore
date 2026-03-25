"""Test forecast generation directly."""

from datetime import date
from src.database.connection import init_db
from src.ai.insights_service import AIInsightsService

print("Testing Forecast Generation Directly")
print("=" * 60)

# Initialize database
init_db()

# Initialize service
service = AIInsightsService()

# Test forecast
system_id = "PROD_ANALYTICS"
print(f"\nGenerating forecast for {system_id}...")

try:
    forecast = service.generate_forecast(system_id, historical_days=60)
    
    print("✓ Forecast generated successfully")
    print(f"\nForecast data:")
    print(f"  System: {forecast['source_system_id']}")
    print(f"  Generated at: {forecast['forecast_generated_at']}")
    print(f"  Historical period: {forecast['historical_period']}")
    print(f"  Predictions: {len(forecast['predictions'])}")
    print(f"  Cached: {forecast.get('cached', False)}")
    
    if forecast['predictions']:
        pred = forecast['predictions'][0]
        print(f"\n  First prediction:")
        print(f"    Date: {pred['date']}")
        print(f"    Count: {pred['predicted_count']}")
        print(f"    Confidence: {pred['confidence_level']}")
        print(f"    Range: {pred['confidence_range']}")
    
except Exception as e:
    print(f"✗ Failed: {e}")
    import traceback
    traceback.print_exc()
