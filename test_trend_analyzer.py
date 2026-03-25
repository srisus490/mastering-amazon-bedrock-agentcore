"""Test TrendAnalyzer directly"""

from datetime import date, timedelta
from src.database.connection import init_db
from src.analytics.trend_analyzer import TrendAnalyzer

def test_analyzer():
    """Test TrendAnalyzer methods directly"""
    
    # Initialize database
    init_db()
    
    analyzer = TrendAnalyzer()
    system_id = "PROD_ANALYTICS"
    
    print(f"Testing TrendAnalyzer with system: {system_id}")
    print("=" * 60)
    
    # Test daily counts
    print("\n1. Testing get_daily_counts...")
    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        counts = analyzer.get_daily_counts(system_id, start_date, end_date)
        print(f"   Success! Got {len(counts)} daily counts")
        if counts:
            print(f"   Sample: {counts[0].to_dict()}")
    except Exception as e:
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test moving average
    print("\n2. Testing calculate_moving_average...")
    try:
        points = analyzer.calculate_moving_average(
            source_system_id=system_id,
            window_days=7,
            end_date=date.today(),
            lookback_days=30
        )
        print(f"   Success! Got {len(points)} data points")
        if points:
            print(f"   Sample: {points[0].to_dict()}")
    except Exception as e:
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test hourly patterns
    print("\n3. Testing get_hourly_patterns...")
    try:
        patterns = analyzer.get_hourly_patterns(system_id, days_back=30)
        print(f"   Success! Got {len(patterns)} patterns")
        if patterns:
            print(f"   Sample: {patterns[0].to_dict()}")
    except Exception as e:
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_analyzer()
