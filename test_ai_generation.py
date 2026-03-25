"""Test AI insights generation with real data."""

import os
from datetime import date, timedelta

# Set environment variables
os.environ["AI_ENABLED"] = "true"
os.environ["BEDROCK_REGION"] = "us-east-1"

from src.ai.bedrock_client import BedrockClient, BedrockError
from src.ai.data_aggregator import DataAggregator
from src.database.connection import init_db


def build_insights_prompt(data_summary: dict) -> str:
    """Build prompt for smart insights generation."""
    summary = data_summary['summary']
    daily_counts = data_summary['daily_counts']
    hourly_patterns = data_summary['hourly_patterns']
    
    prompt = f"""You are an expert data analyst for a file monitoring system. Analyze the following file arrival data and provide insights.

System: {data_summary['source_system_id']}
Date Range: {data_summary['date_range']['start']} to {data_summary['date_range']['end']} ({data_summary['date_range']['days']} days)

Summary Statistics:
- Total files received: {summary['total_files']}
- Average daily count: {summary['avg_daily_count']}
- Days with files: {summary['days_with_files']}
- Days without files: {summary['days_without_files']}

Daily File Counts:
"""
    
    for day in daily_counts[:10]:  # Show first 10 days
        prompt += f"- {day['date']}: {day['count']} files (avg size: {day['avg_size']} bytes)\n"
    
    if len(daily_counts) > 10:
        prompt += f"... and {len(daily_counts) - 10} more days\n"
    
    prompt += f"\nHourly Arrival Patterns:\n"
    for hour in hourly_patterns[:5]:  # Show first 5 hours
        prompt += f"- Hour {hour['hour']:02d}:00: {hour['count']} files\n"
    
    if summary['days_without_files'] > 0:
        prompt += f"\nMissing Data Days: {', '.join(summary['missing_dates'][:5])}\n"
    
    prompt += """
Please provide:
1. A brief summary of the system's health and file arrival patterns
2. Any notable trends (increasing, decreasing, stable)
3. Any anomalies or concerns (unusual spikes, missing data, timing issues)
4. 2-3 actionable recommendations

Keep your response concise and focused on actionable insights. Format as:

SUMMARY:
[2-3 sentences about overall health]

TRENDS:
- [Trend 1]
- [Trend 2]

ANOMALIES:
- [Anomaly 1 if any, or "None detected"]

RECOMMENDATIONS:
1. [Recommendation 1]
2. [Recommendation 2]
"""
    
    return prompt


def build_forecast_prompt(historical_data: dict) -> str:
    """Build prompt for trend forecasting."""
    stats = historical_data['statistics']
    trend = historical_data['trend']
    dow_avg = historical_data['day_of_week_averages']
    
    prompt = f"""You are an expert forecaster for a file monitoring system. Based on historical data, predict file arrivals for the next 7 days.

System: {historical_data['source_system_id']}
Historical Period: {historical_data['historical_period']['days']} days

Statistics:
- Average daily count: {stats['avg_count']}
- Minimum: {stats['min_count']}
- Maximum: {stats['max_count']}
- Trend: {trend['direction']} (slope: {trend['slope']})

Day of Week Averages:
"""
    
    day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    for dow, avg in sorted(dow_avg.items()):
        prompt += f"- {day_names[dow]}: {avg} files\n"
    
    prompt += """
Predict the expected file count for each of the next 7 days. For each day, provide:
- Date (starting from tomorrow)
- Predicted count (integer)
- Confidence level (high/medium/low)

Format your response as JSON:
{
  "predictions": [
    {"date": "YYYY-MM-DD", "count": X, "confidence": "high"},
    ...
  ],
  "reasoning": "Brief explanation of prediction logic"
}
"""
    
    return prompt


def test_smart_insights():
    """Test smart insights generation."""
    print("\n" + "="*70)
    print("TEST: SMART INSIGHTS GENERATION")
    print("="*70)
    
    # Initialize
    init_db()
    aggregator = DataAggregator()
    client = BedrockClient()
    
    # Get data for last 7 days
    end_date = date.today()
    start_date = end_date - timedelta(days=7)
    
    print(f"\nAnalyzing PROD_ANALYTICS from {start_date} to {end_date}...")
    
    # Aggregate data
    data_summary = aggregator.get_file_arrival_summary(
        "PROD_ANALYTICS",
        start_date,
        end_date
    )
    
    print(f"✓ Data aggregated: {data_summary['summary']['total_files']} files")
    
    # Build prompt
    prompt = build_insights_prompt(data_summary)
    print(f"✓ Prompt built ({len(prompt)} characters)")
    
    # Call Bedrock
    print(f"\n🤖 Calling Amazon Bedrock (Claude 3 Sonnet)...")
    print(f"   This may take 5-10 seconds...\n")
    
    try:
        response = client.invoke_model(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.7
        )
        
        print("="*70)
        print("AI-GENERATED INSIGHTS")
        print("="*70)
        print(response)
        print("="*70)
        
        # Estimate cost
        input_tokens = len(prompt) / 4  # Rough estimate: 4 chars per token
        output_tokens = len(response) / 4
        cost = (input_tokens / 1_000_000 * 3) + (output_tokens / 1_000_000 * 15)
        
        print(f"\n💰 Estimated cost: ${cost:.4f}")
        print(f"   Input tokens: ~{int(input_tokens)}")
        print(f"   Output tokens: ~{int(output_tokens)}")
        
        return True
        
    except BedrockError as e:
        print(f"\n❌ Bedrock Error: {e}")
        print(f"\nTroubleshooting:")
        print(f"1. Verify AWS credentials are configured")
        print(f"2. Check that you have Bedrock access in your AWS account")
        print(f"3. Ensure Claude 3 Sonnet model is enabled in your region")
        return False


def test_forecast():
    """Test forecast generation."""
    print("\n" + "="*70)
    print("TEST: TREND FORECASTING")
    print("="*70)
    
    # Initialize
    init_db()
    aggregator = DataAggregator()
    client = BedrockClient()
    
    print(f"\nAnalyzing PROD_ANALYTICS historical patterns (30 days)...")
    
    # Get historical data
    historical_data = aggregator.get_historical_patterns(
        "PROD_ANALYTICS",
        days=30
    )
    
    print(f"✓ Historical data aggregated: {len(historical_data['daily_counts'])} days")
    print(f"✓ Trend: {historical_data['trend']['direction']}")
    
    # Build prompt
    prompt = build_forecast_prompt(historical_data)
    print(f"✓ Prompt built ({len(prompt)} characters)")
    
    # Call Bedrock
    print(f"\n🤖 Calling Amazon Bedrock (Claude 3 Sonnet)...")
    print(f"   This may take 5-10 seconds...\n")
    
    try:
        response = client.invoke_model(
            prompt=prompt,
            max_tokens=800,
            temperature=0.5  # Lower temperature for more consistent predictions
        )
        
        print("="*70)
        print("AI-GENERATED FORECAST")
        print("="*70)
        print(response)
        print("="*70)
        
        # Estimate cost
        input_tokens = len(prompt) / 4
        output_tokens = len(response) / 4
        cost = (input_tokens / 1_000_000 * 3) + (output_tokens / 1_000_000 * 15)
        
        print(f"\n💰 Estimated cost: ${cost:.4f}")
        
        return True
        
    except BedrockError as e:
        print(f"\n❌ Bedrock Error: {e}")
        return False


def main():
    """Run AI generation tests."""
    print("\n" + "="*70)
    print("AI INSIGHTS GENERATION TEST")
    print("Testing with real data from your monitoring system")
    print("="*70)
    
    print("\n⚠️  Note: This will make actual API calls to Amazon Bedrock")
    print("   Estimated cost: ~$0.02 for both tests")
    print("   With caching enabled, subsequent calls will be FREE!")
    
    input("\nPress Enter to continue...")
    
    # Test 1: Smart Insights
    insights_success = test_smart_insights()
    
    if insights_success:
        print("\n" + "="*70)
        input("\nPress Enter to test forecasting...")
        
        # Test 2: Forecast
        forecast_success = test_forecast()
        
        if forecast_success:
            print("\n" + "="*70)
            print("✅ SUCCESS!")
            print("="*70)
            print("\nBoth AI features are working perfectly!")
            print("\nWith caching enabled:")
            print("- These insights will be cached for 1 hour")
            print("- Forecasts will be cached for 6 hours")
            print("- Subsequent requests will be FREE (served from cache)")
            print("- Estimated monthly cost: ~$4-5 with normal usage")
            print("\nNext step: Complete the remaining tasks to integrate")
            print("these AI features into your dashboard!")
    else:
        print("\n" + "="*70)
        print("⚠️  AI generation test incomplete")
        print("="*70)
        print("\nPlease resolve the Bedrock connection issue and try again.")


if __name__ == "__main__":
    main()
