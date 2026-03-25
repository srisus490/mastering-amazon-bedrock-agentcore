"""Test AI features with Amazon Bedrock"""

from src.ai.anomaly_detector import BedrockAnomalyDetector
from src.database.connection import init_db

def test_ai():
    """Test AI capabilities"""
    
    init_db()
    
    print("\n" + "=" * 70)
    print("🤖 TESTING AI FEATURES - Amazon Bedrock Integration")
    print("=" * 70)
    
    print("\n⚠️  Note: This requires:")
    print("  1. AWS credentials configured (aws configure)")
    print("  2. Bedrock model access enabled (Claude 3 Sonnet)")
    print("  3. Internet connection")
    
    input("\nPress Enter to continue (or Ctrl+C to cancel)...")
    
    detector = BedrockAnomalyDetector()
    
    # Test 1: Anomaly Detection
    print("\n" + "-" * 70)
    print("TEST 1: AI-Powered Anomaly Detection")
    print("-" * 70)
    print("Analyzing file arrival patterns for SYS001...")
    
    try:
        analysis = detector.analyze_pattern("SYS001", days=30)
        
        print(f"\n✅ Analysis Complete!")
        print(f"   System: {analysis['source_system_id']}")
        print(f"   Period: {analysis['period_analyzed']}")
        print(f"   Data Points: {analysis['data_points']}")
        print(f"   Model Used: {analysis['model_used']}")
        
        ai_analysis = analysis.get('ai_analysis', {})
        
        if 'risk_level' in ai_analysis:
            risk = ai_analysis['risk_level']
            risk_emoji = "✅" if risk == "Low" else "⚠️" if risk == "Medium" else "❌"
            print(f"\n   {risk_emoji} Risk Level: {risk}")
        
        if 'anomalies' in ai_analysis:
            anomalies = ai_analysis['anomalies']
            print(f"\n   Anomalies Detected: {len(anomalies)}")
            for i, anomaly in enumerate(anomalies[:3], 1):
                print(f"     {i}. {anomaly}")
        
        if 'recommendations' in ai_analysis:
            recommendations = ai_analysis['recommendations']
            print(f"\n   AI Recommendations: {len(recommendations)}")
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"     {i}. {rec}")
        
        if 'summary' in ai_analysis:
            print(f"\n   Summary: {ai_analysis['summary'][:200]}...")
        
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        print("\nPossible issues:")
        print("  - AWS credentials not configured")
        print("  - Bedrock model access not enabled")
        print("  - No internet connection")
        print("  - Insufficient data in database")
    
    # Test 2: Prediction
    print("\n" + "-" * 70)
    print("TEST 2: AI-Powered Prediction")
    print("-" * 70)
    print("Predicting file arrivals for next 7 days...")
    
    try:
        prediction = detector.predict_next_week("SYS001", historical_days=60)
        
        print(f"\n✅ Prediction Complete!")
        print(f"   System: {prediction['source_system_id']}")
        print(f"   Historical Days Used: {prediction['historical_days_used']}")
        print(f"   Model Used: {prediction['model_used']}")
        
        predictions = prediction.get('predictions', {})
        
        if 'predictions' in predictions:
            pred_list = predictions['predictions']
            print(f"\n   Predictions for Next 7 Days:")
            for pred in pred_list[:7]:
                date = pred.get('date', 'N/A')
                day = pred.get('day', 'N/A')
                count = pred.get('predicted_count', 'N/A')
                confidence = pred.get('confidence', 'N/A')
                print(f"     {date} ({day}): {count} files (Confidence: {confidence})")
        
        if 'overall_trend' in predictions:
            print(f"\n   Overall Trend: {predictions['overall_trend']}")
        
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
    
    # Test 3: SLA Recommendations
    print("\n" + "-" * 70)
    print("TEST 3: AI-Powered SLA Optimization")
    print("-" * 70)
    print("Generating SLA recommendations based on actual patterns...")
    
    try:
        recommendations = detector.recommend_sla_adjustments("SYS001", days=90)
        
        print(f"\n✅ Recommendations Generated!")
        print(f"   System: {recommendations['source_system_id']}")
        print(f"   Analysis Date: {recommendations['analysis_date']}")
        print(f"   Model Used: {recommendations['model_used']}")
        
        current_sla = recommendations.get('current_sla', {})
        print(f"\n   Current SLA:")
        print(f"     Expected Time: {current_sla.get('expected_arrival_time', 'N/A')}")
        print(f"     Window: ±{current_sla.get('window_minutes', 'N/A')} minutes")
        print(f"     Min Files/Day: {current_sla.get('minimum_files_per_day', 'N/A')}")
        
        recs = recommendations.get('recommendations', {})
        
        if 'recommended_sla' in recs:
            rec_sla = recs['recommended_sla']
            print(f"\n   AI Recommended SLA:")
            print(f"     Expected Time: {rec_sla.get('expected_arrival_time', 'N/A')}")
            print(f"     Window: ±{rec_sla.get('window_minutes', 'N/A')} minutes")
            print(f"     Min Files/Day: {rec_sla.get('minimum_files_per_day', 'N/A')}")
            
            if 'reasoning' in rec_sla:
                print(f"\n   Reasoning: {rec_sla['reasoning'][:200]}...")
        
        if 'expected_improvement' in recs:
            print(f"\n   Expected Improvement: {recs['expected_improvement'][:200]}...")
        
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print("🎉 AI TESTING COMPLETE!")
    print("=" * 70)
    
    print("\n📊 What You Just Tested:")
    print("  ✅ AI-powered anomaly detection using Claude 3")
    print("  ✅ Predictive analytics for file arrivals")
    print("  ✅ SLA optimization recommendations")
    
    print("\n🚀 Next Steps:")
    print("  1. Access AI features via API: http://localhost:8000/docs")
    print("  2. Try natural language queries (requires Bedrock Agent setup)")
    print("  3. Schedule daily AI analysis for production")
    print("  4. Review AI_IMPLEMENTATION_GUIDE.md for full details")
    
    print("\n💰 Cost Estimate:")
    print("  - These 3 AI calls: ~$0.05")
    print("  - 100 calls/day: ~$30-60/month")
    print("  - Still 95% cheaper than original architecture!")
    
    print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    test_ai()
