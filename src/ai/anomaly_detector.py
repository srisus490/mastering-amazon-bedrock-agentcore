"""AI-powered anomaly detection using Amazon Bedrock"""

import json
from datetime import date, timedelta
from typing import Dict, List, Optional

import boto3

from src.analytics.trend_analyzer import TrendAnalyzer
from src.core.logging import get_logger

logger = get_logger(__name__)


class BedrockAnomalyDetector:
    """
    Detect anomalies in file arrival patterns using Amazon Bedrock.
    
    Uses Claude 3 to analyze historical patterns and identify:
    - Unusual file counts
    - Missing files
    - Timing anomalies
    - Trend changes
    """
    
    def __init__(
        self,
        model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0",
        region: str = "us-east-1",
    ):
        """
        Initialize Bedrock anomaly detector.
        
        Args:
            model_id: Bedrock model ID to use
            region: AWS region
        """
        self.model_id = model_id
        self.bedrock = boto3.client('bedrock-runtime', region_name=region)
        logger.info("BedrockAnomalyDetector initialized", model_id=model_id)
    
    def analyze_pattern(
        self,
        source_system_id: str,
        days: int = 30,
    ) -> Dict:
        """
        Use AI to detect anomalies in file arrival patterns.
        
        Args:
            source_system_id: Source system to analyze
            days: Number of days of history to analyze
            
        Returns:
            Dictionary with AI analysis results
        """
        logger.info(
            "Analyzing pattern with AI",
            source_system_id=source_system_id,
            days=days,
        )
        
        try:
            # Get historical data
            analyzer = TrendAnalyzer()
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            daily_counts = analyzer.get_daily_counts(
                source_system_id, start_date, end_date
            )
            
            # Prepare data for AI
            data_summary = [
                {
                    "date": dc.arrival_date.isoformat(),
                    "count": dc.file_count,
                    "total_size_mb": round(dc.total_size_bytes / (1024 * 1024), 2),
                    "first_arrival": dc.first_arrival.isoformat() if dc.first_arrival else None,
                    "last_arrival": dc.last_arrival.isoformat() if dc.last_arrival else None,
                }
                for dc in daily_counts
            ]
            
            # Calculate basic statistics
            counts = [d["count"] for d in data_summary]
            avg_count = sum(counts) / len(counts) if counts else 0
            max_count = max(counts) if counts else 0
            min_count = min(counts) if counts else 0
            
            # Create prompt for Bedrock
            prompt = f"""You are an expert data analyst specializing in file monitoring systems. Analyze this file arrival pattern for system {source_system_id}.

HISTORICAL DATA (last {days} days):
{json.dumps(data_summary, indent=2)}

STATISTICS:
- Average daily files: {avg_count:.1f}
- Maximum: {max_count}
- Minimum: {min_count}
- Days with data: {len(data_summary)}

ANALYSIS REQUIRED:
1. **Anomalies**: Identify any unusual patterns, spikes, or drops in file counts
2. **Missing Data**: Detect days with zero or unexpectedly low file counts
3. **Timing Issues**: Analyze first/last arrival times for consistency
4. **Trends**: Identify upward or downward trends
5. **Risk Assessment**: Rate the overall health (Low/Medium/High risk)
6. **Recommendations**: Suggest specific actions or SLA adjustments

Provide a structured JSON response with these sections:
{{
  "anomalies": [list of detected anomalies with dates and descriptions],
  "missing_data_days": [list of dates with missing or low data],
  "timing_issues": [list of timing-related concerns],
  "trend_analysis": "description of overall trend",
  "risk_level": "Low/Medium/High",
  "recommendations": [list of specific actionable recommendations],
  "summary": "brief executive summary"
}}"""

            # Call Bedrock
            logger.debug("Calling Bedrock API", model_id=self.model_id)
            
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 3000,
                    "temperature": 0.3,  # Lower temperature for more consistent analysis
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            )
            
            result = json.loads(response['body'].read())
            ai_response = result['content'][0]['text']
            
            # Try to parse JSON from response
            try:
                # Extract JSON from markdown code blocks if present
                if "```json" in ai_response:
                    json_start = ai_response.find("```json") + 7
                    json_end = ai_response.find("```", json_start)
                    ai_analysis = json.loads(ai_response[json_start:json_end].strip())
                elif "```" in ai_response:
                    json_start = ai_response.find("```") + 3
                    json_end = ai_response.find("```", json_start)
                    ai_analysis = json.loads(ai_response[json_start:json_end].strip())
                else:
                    # Try to parse the whole response
                    ai_analysis = json.loads(ai_response)
            except json.JSONDecodeError:
                # If JSON parsing fails, return raw text
                ai_analysis = {
                    "raw_analysis": ai_response,
                    "summary": "AI analysis completed (see raw_analysis for details)"
                }
            
            logger.info(
                "AI analysis completed",
                source_system_id=source_system_id,
                risk_level=ai_analysis.get("risk_level", "Unknown"),
            )
            
            return {
                "source_system_id": source_system_id,
                "analysis_date": date.today().isoformat(),
                "period_analyzed": f"{start_date} to {end_date}",
                "data_points": len(data_summary),
                "statistics": {
                    "avg_daily_files": round(avg_count, 2),
                    "max_files": max_count,
                    "min_files": min_count,
                },
                "ai_analysis": ai_analysis,
                "model_used": self.model_id,
            }
            
        except Exception as e:
            logger.error(
                "Failed to analyze pattern",
                source_system_id=source_system_id,
                error=str(e),
            )
            raise
    
    def predict_next_week(
        self,
        source_system_id: str,
        historical_days: int = 60,
    ) -> Dict:
        """
        Use AI to predict file arrivals for the next 7 days.
        
        Args:
            source_system_id: Source system to predict for
            historical_days: Days of history to use for prediction
            
        Returns:
            Dictionary with predictions
        """
        logger.info(
            "Predicting next week with AI",
            source_system_id=source_system_id,
        )
        
        try:
            # Get historical data
            analyzer = TrendAnalyzer()
            end_date = date.today()
            start_date = end_date - timedelta(days=historical_days)
            
            daily_counts = analyzer.get_daily_counts(
                source_system_id, start_date, end_date
            )
            
            # Prepare data
            data_summary = [
                {
                    "date": dc.arrival_date.isoformat(),
                    "day_of_week": dc.arrival_date.strftime("%A"),
                    "count": dc.file_count,
                }
                for dc in daily_counts
            ]
            
            # Create prediction prompt
            prompt = f"""You are a predictive analytics expert. Based on this historical file arrival data for system {source_system_id}, predict the expected file counts for the next 7 days.

HISTORICAL DATA (last {historical_days} days):
{json.dumps(data_summary, indent=2)}

Consider:
- Day of week patterns
- Recent trends
- Seasonal variations
- Any anomalies

Provide predictions in JSON format:
{{
  "predictions": [
    {{"date": "YYYY-MM-DD", "day": "Monday", "predicted_count": 10, "confidence": "High/Medium/Low", "reasoning": "brief explanation"}},
    ...
  ],
  "overall_trend": "description",
  "confidence_level": "High/Medium/Low"
}}"""

            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 2000,
                    "temperature": 0.3,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            )
            
            result = json.loads(response['body'].read())
            ai_response = result['content'][0]['text']
            
            # Parse JSON response
            try:
                if "```json" in ai_response:
                    json_start = ai_response.find("```json") + 7
                    json_end = ai_response.find("```", json_start)
                    predictions = json.loads(ai_response[json_start:json_end].strip())
                else:
                    predictions = json.loads(ai_response)
            except json.JSONDecodeError:
                predictions = {"raw_prediction": ai_response}
            
            logger.info(
                "Prediction completed",
                source_system_id=source_system_id,
            )
            
            return {
                "source_system_id": source_system_id,
                "prediction_date": date.today().isoformat(),
                "historical_days_used": historical_days,
                "predictions": predictions,
                "model_used": self.model_id,
            }
            
        except Exception as e:
            logger.error(
                "Failed to predict",
                source_system_id=source_system_id,
                error=str(e),
            )
            raise
    
    def recommend_sla_adjustments(
        self,
        source_system_id: str,
        days: int = 90,
    ) -> Dict:
        """
        Use AI to recommend SLA adjustments based on actual patterns.
        
        Args:
            source_system_id: Source system to analyze
            days: Days of history to analyze
            
        Returns:
            Dictionary with SLA recommendations
        """
        logger.info(
            "Generating SLA recommendations",
            source_system_id=source_system_id,
        )
        
        try:
            # Get current SLA
            from src.sla.evaluator import SLAEvaluator
            evaluator = SLAEvaluator()
            current_sla = evaluator.get_sla_definition(source_system_id, date.today())
            
            if not current_sla:
                return {
                    "error": "No SLA definition found for this system",
                    "source_system_id": source_system_id,
                }
            
            # Get historical patterns
            analyzer = TrendAnalyzer()
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            hourly_patterns = analyzer.get_hourly_patterns(
                source_system_id, start_date, end_date
            )
            daily_counts = analyzer.get_daily_counts(
                source_system_id, start_date, end_date
            )
            
            # Prepare data
            pattern_summary = [
                {
                    "day_of_week": p.day_of_week,
                    "hour": p.hour,
                    "avg_count": round(p.avg_count, 2),
                }
                for p in hourly_patterns[:50]  # Top 50 patterns
            ]
            
            daily_summary = [
                {"date": dc.arrival_date.isoformat(), "count": dc.file_count}
                for dc in daily_counts
            ]
            
            prompt = f"""You are an SLA optimization expert. Analyze the actual file arrival patterns and recommend optimal SLA settings.

CURRENT SLA:
- Expected arrival time: {current_sla.expected_arrival_time}
- Window: ±{current_sla.expected_arrival_window_minutes} minutes
- Minimum files per day: {current_sla.minimum_files_per_day}

ACTUAL PATTERNS (last {days} days):
Hourly patterns: {json.dumps(pattern_summary, indent=2)}
Daily counts: {json.dumps(daily_summary[-30:], indent=2)}

Recommend:
1. Optimal arrival time window
2. Appropriate tolerance window
3. Realistic minimum file count
4. Any other SLA parameters

Provide JSON response:
{{
  "recommended_sla": {{
    "expected_arrival_time": "HH:MM:SS",
    "window_minutes": number,
    "minimum_files_per_day": number,
    "reasoning": "explanation"
  }},
  "current_vs_recommended": "comparison",
  "expected_improvement": "description of benefits"
}}"""

            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 2000,
                    "temperature": 0.3,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            )
            
            result = json.loads(response['body'].read())
            ai_response = result['content'][0]['text']
            
            # Parse response
            try:
                if "```json" in ai_response:
                    json_start = ai_response.find("```json") + 7
                    json_end = ai_response.find("```", json_start)
                    recommendations = json.loads(ai_response[json_start:json_end].strip())
                else:
                    recommendations = json.loads(ai_response)
            except json.JSONDecodeError:
                recommendations = {"raw_recommendation": ai_response}
            
            logger.info(
                "SLA recommendations generated",
                source_system_id=source_system_id,
            )
            
            return {
                "source_system_id": source_system_id,
                "analysis_date": date.today().isoformat(),
                "current_sla": {
                    "expected_arrival_time": str(current_sla.expected_arrival_time),
                    "window_minutes": current_sla.expected_arrival_window_minutes,
                    "minimum_files_per_day": current_sla.minimum_files_per_day,
                },
                "recommendations": recommendations,
                "model_used": self.model_id,
            }
            
        except Exception as e:
            logger.error(
                "Failed to generate recommendations",
                source_system_id=source_system_id,
                error=str(e),
            )
            raise
