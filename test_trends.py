"""Test trend analysis functionality"""

from datetime import date, timedelta

from src.analytics.trend_analyzer import TrendAnalyzer
from src.database.connection import init_db

def test_trends():
    """Test trend analysis"""
    
    init_db()
    
    print("Testing Trend Analysis...")
    print("=" * 50)
    
    analyzer = TrendAnalyzer()
    
    end_date = date.today()
    start_date = end_date - timedelta(days=7)
    
    # Test daily counts
    print("\n1. Testing Daily Counts...")
    counts = analyzer.get_daily_counts("SYS001", start_date, end_date)
    print(f"   ✅ Retrieved {len(counts)} days of data")
    if counts:
        latest = counts[-1]
        print(f"   Latest: {latest.arrival_date} - {latest.file_count} files")
    
    # Test moving averages
    print("\n2. Testing Moving Averages...")
    ma_points = analyzer.calculate_moving_average("SYS001", start_date, end_date)
    print(f"   ✅ Retrieved {len(ma_points)} data points")
    if ma_points:
        latest = ma_points[-1]
        print(f"   Latest: 7-day avg = {latest.moving_avg_7d:.2f}, 30-day avg = {latest.moving_avg_30d:.2f}")
    
    # Test hourly patterns
    print("\n3. Testing Hourly Patterns...")
    patterns = analyzer.get_hourly_patterns("SYS001", start_date, end_date)
    print(f"   ✅ Retrieved {len(patterns)} hourly patterns")
    if patterns:
        print(f"   Sample: Day {patterns[0].day_of_week}, Hour {patterns[0].hour} - Avg {patterns[0].avg_count:.2f} files")
    
    # Test all systems summary
    print("\n4. Testing All Systems Summary...")
    summary = analyzer.get_all_systems_summary()
    print(f"   ✅ Retrieved summary for {len(summary)} systems")
    if summary:
        print(f"   First system: {summary[0]}")
    
    print("\n" + "=" * 50)
    print("Trend analysis tests complete!")

if __name__ == "__main__":
    test_trends()
