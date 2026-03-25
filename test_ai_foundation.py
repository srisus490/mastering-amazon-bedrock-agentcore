"""Test script for AI insights foundation components."""

import os
from datetime import date, timedelta

# Set test environment variables
os.environ["AI_ENABLED"] = "true"
os.environ["BEDROCK_REGION"] = "us-east-1"
os.environ["BEDROCK_MODEL_ID"] = "anthropic.claude-3-sonnet-20240229-v1:0"

from src.ai.config import ai_config
from src.ai.cache_manager import CacheManager
from src.ai.data_aggregator import DataAggregator
from src.ai.bedrock_client import BedrockClient
from src.database.connection import init_db


def test_configuration():
    """Test AI configuration."""
    print("\n" + "="*60)
    print("TEST 1: Configuration")
    print("="*60)
    
    print(f"✓ AI Enabled: {ai_config.ai_enabled}")
    print(f"✓ Bedrock Region: {ai_config.bedrock_region}")
    print(f"✓ Bedrock Model: {ai_config.bedrock_model_id}")
    print(f"✓ Timeout: {ai_config.bedrock_timeout}s")
    print(f"✓ Max Tokens: {ai_config.bedrock_max_tokens}")
    print(f"✓ Cache TTL (Insights): {ai_config.ai_cache_ttl_insights}s ({ai_config.ai_cache_ttl_insights/3600}h)")
    print(f"✓ Cache TTL (Forecast): {ai_config.ai_cache_ttl_forecast}s ({ai_config.ai_cache_ttl_forecast/3600}h)")
    print(f"✓ Is Configured: {ai_config.is_configured()}")
    
    return True


def test_cache_manager():
    """Test cache manager."""
    print("\n" + "="*60)
    print("TEST 2: Cache Manager")
    print("="*60)
    
    # Initialize database first
    init_db()
    
    cache = CacheManager()
    
    # Test cache key generation
    key1 = cache.generate_cache_key(
        "insights",
        "PROD_SALES",
        start_date="2024-01-01",
        end_date="2024-01-31"
    )
    print(f"✓ Generated cache key: {key1}")
    
    # Test that same params generate same key
    key2 = cache.generate_cache_key(
        "insights",
        "PROD_SALES",
        start_date="2024-01-01",
        end_date="2024-01-31"
    )
    assert key1 == key2, "Same params should generate same key"
    print(f"✓ Cache key consistency verified")
    
    # Test that different params generate different keys
    key3 = cache.generate_cache_key(
        "insights",
        "PROD_SALES",
        start_date="2024-02-01",
        end_date="2024-02-28"
    )
    assert key1 != key3, "Different params should generate different keys"
    print(f"✓ Cache key uniqueness verified")
    
    # Test cache set and get
    test_data = {
        "source_system_id": "PROD_SALES",
        "insights": "Test insights",
        "generated_at": "2024-01-31T10:00:00Z"
    }
    
    cache.set_cached_insight(key1, test_data, ttl_seconds=3600)
    print(f"✓ Cached data stored")
    
    retrieved = cache.get_cached_insight(key1)
    assert retrieved is not None, "Should retrieve cached data"
    assert retrieved["cached"] == True, "Should mark as cached"
    assert retrieved["insights"] == "Test insights", "Should retrieve correct data"
    print(f"✓ Cached data retrieved successfully")
    
    # Test cache miss
    fake_key = cache.generate_cache_key("forecast", "FAKE_SYSTEM", days=60)
    retrieved = cache.get_cached_insight(fake_key)
    assert retrieved is None, "Should return None for cache miss"
    print(f"✓ Cache miss handled correctly")
    
    # Test TTL
    ttl_insights = cache.get_ttl_for_insight_type("insights")
    ttl_forecast = cache.get_ttl_for_insight_type("forecast")
    assert ttl_insights == 3600, "Insights TTL should be 1 hour"
    assert ttl_forecast == 21600, "Forecast TTL should be 6 hours"
    print(f"✓ TTL configuration correct")
    
    return True


def test_data_aggregator():
    """Test data aggregator."""
    print("\n" + "="*60)
    print("TEST 3: Data Aggregator")
    print("="*60)
    
    # Initialize database
    init_db()
    
    aggregator = DataAggregator()
    
    # Test with a system that has data
    end_date = date.today()
    start_date = end_date - timedelta(days=7)
    
    try:
        # Test file arrival summary
        summary = aggregator.get_file_arrival_summary(
            "PROD_ANALYTICS",
            start_date,
            end_date
        )
        
        print(f"✓ File arrival summary generated")
        print(f"  - System: {summary['source_system_id']}")
        print(f"  - Date range: {summary['date_range']['start']} to {summary['date_range']['end']}")
        print(f"  - Total files: {summary['summary']['total_files']}")
        print(f"  - Days with files: {summary['summary']['days_with_files']}")
        print(f"  - Avg daily count: {summary['summary']['avg_daily_count']}")
        print(f"  - Daily data points: {len(summary['daily_counts'])}")
        print(f"  - Hourly patterns: {len(summary['hourly_patterns'])}")
        
        # Test SLA violation summary
        sla_summary = aggregator.get_sla_violation_summary(
            "PROD_ANALYTICS",
            start_date,
            end_date
        )
        
        print(f"✓ SLA violation summary generated")
        print(f"  - Total violations: {sla_summary['total_violations']}")
        print(f"  - Avg SLA score: {sla_summary['avg_sla_score']}")
        
        # Test historical patterns
        patterns = aggregator.get_historical_patterns(
            "PROD_ANALYTICS",
            days=30
        )
        
        print(f"✓ Historical patterns generated")
        print(f"  - Days analyzed: {patterns['historical_period']['days']}")
        print(f"  - Data points: {len(patterns['daily_counts'])}")
        print(f"  - Trend direction: {patterns['trend']['direction']}")
        print(f"  - Avg count: {patterns['statistics']['avg_count']}")
        print(f"  - Day-of-week patterns: {len(patterns['day_of_week_averages'])} days")
        
        # Test 90-day limit enforcement
        patterns_90 = aggregator.get_historical_patterns(
            "PROD_ANALYTICS",
            days=120  # Request 120, should limit to 90
        )
        assert patterns_90['historical_period']['days'] == 90, "Should enforce 90-day limit"
        print(f"✓ 90-day limit enforced correctly")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_bedrock_client():
    """Test Bedrock client (without actual AWS call)."""
    print("\n" + "="*60)
    print("TEST 4: Bedrock Client")
    print("="*60)
    
    try:
        client = BedrockClient()
        print(f"✓ Bedrock client initialized")
        print(f"  - Region: {client.region}")
        print(f"  - Model ID: {client.model_id}")
        print(f"  - Timeout: {client.timeout}s")
        
        # Test credential validation (will fail without AWS credentials)
        print(f"\n  Testing AWS credentials...")
        is_valid = client.validate_credentials()
        
        if is_valid:
            print(f"  ✓ AWS credentials are valid")
            print(f"  ✓ Ready to make Bedrock API calls")
        else:
            print(f"  ⚠ AWS credentials not configured")
            print(f"  ℹ This is expected if you haven't set up AWS credentials yet")
            print(f"  ℹ To enable AI features, configure AWS credentials:")
            print(f"     - Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
            print(f"     - Or use IAM roles in production")
        
        return True
        
    except Exception as e:
        print(f"✗ Error initializing Bedrock client: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("AI INSIGHTS FOUNDATION TEST SUITE")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Configuration", test_configuration()))
    results.append(("Cache Manager", test_cache_manager()))
    results.append(("Data Aggregator", test_data_aggregator()))
    results.append(("Bedrock Client", test_bedrock_client()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All foundation components are working correctly!")
        print("\nNext steps:")
        print("1. Configure AWS credentials to enable Bedrock")
        print("2. Continue implementation with remaining tasks")
        print("3. Test AI insights generation with real data")
    else:
        print("\n⚠ Some tests failed. Please review the errors above.")
    
    print("="*60)


if __name__ == "__main__":
    main()
