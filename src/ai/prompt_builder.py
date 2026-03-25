"""Prompt builder for AI insights generation."""

import re
from typing import Dict

from src.ai.logger import ai_logger


class PromptBuilder:
    """
    Builds prompts for different AI tasks.
    
    Sanitizes input data to prevent prompt injection and constructs
    structured prompts optimized for Claude 3 Sonnet.
    """
    
    def __init__(self):
        """Initialize prompt builder."""
        ai_logger.info("PromptBuilder initialized")
    
    def sanitize_text(self, text: str) -> str:
        """
        Sanitize text to prevent prompt injection.
        
        Removes or escapes special characters that could be used
        for prompt manipulation.
        
        Args:
            text: Text to sanitize
            
        Returns:
            Sanitized text
        """
        if not isinstance(text, str):
            text = str(text)
        
        # Remove control characters
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        # Escape potential prompt injection patterns
        text = text.replace('\\n\\n', ' ')
        text = text.replace('Human:', 'Human ')
        text = text.replace('Assistant:', 'Assistant ')
        text = text.replace('<|', '< |')
        text = text.replace('|>', '| >')
        
        return text.strip()
    
    def build_insights_prompt(self, data_summary: Dict) -> str:
        """
        Build prompt for smart insights generation.
        
        Args:
            data_summary: Aggregated file arrival data
            
        Returns:
            Formatted prompt string
        """
        summary = data_summary['summary']
        daily_counts = data_summary['daily_counts']
        hourly_patterns = data_summary['hourly_patterns']
        system_id = self.sanitize_text(data_summary['source_system_id'])
        
        prompt = f"""You are an expert data analyst for a file monitoring system. Analyze the following file arrival data and provide insights.

System: {system_id}
Date Range: {data_summary['date_range']['start']} to {data_summary['date_range']['end']} ({data_summary['date_range']['days']} days)

Summary Statistics:
- Total files received: {summary['total_files']}
- Average daily count: {summary['avg_daily_count']}
- Days with files: {summary['days_with_files']}
- Days without files: {summary['days_without_files']}

Daily File Counts:
"""
        
        # Add daily counts (limit to 10 for token efficiency)
        for day in daily_counts[:10]:
            prompt += f"- {day['date']}: {day['count']} files (avg size: {day['avg_size']} bytes)\n"
        
        if len(daily_counts) > 10:
            prompt += f"... and {len(daily_counts) - 10} more days\n"
        
        # Add hourly patterns
        prompt += f"\nHourly Arrival Patterns:\n"
        for hour in hourly_patterns[:8]:  # Show top 8 hours
            prompt += f"- Hour {hour['hour']:02d}:00: {hour['count']} files\n"
        
        # Add missing dates if any
        if summary['days_without_files'] > 0 and summary['missing_dates']:
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
        
        ai_logger.debug(
            "Insights prompt built",
            system_id=system_id,
            prompt_length=len(prompt)
        )
        
        return prompt
    
    def build_forecast_prompt(self, historical_data: Dict) -> str:
        """
        Build prompt for trend forecasting.
        
        Args:
            historical_data: Historical file arrival patterns
            
        Returns:
            Formatted prompt string
        """
        stats = historical_data['statistics']
        trend = historical_data['trend']
        dow_avg = historical_data['day_of_week_averages']
        system_id = self.sanitize_text(historical_data['source_system_id'])
        
        prompt = f"""You are an expert forecaster for a file monitoring system. Based on historical data, predict file arrivals for the next 7 days.

System: {system_id}
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
        
        ai_logger.debug(
            "Forecast prompt built",
            system_id=system_id,
            prompt_length=len(prompt)
        )
        
        return prompt
    
    def build_root_cause_prompt(self, violations: Dict, context: Dict) -> str:
        """
        Build prompt for root cause analysis.
        
        Args:
            violations: SLA violation data
            context: Additional context (file arrival patterns)
            
        Returns:
            Formatted prompt string
        """
        system_id = self.sanitize_text(violations['source_system_id'])
        total_violations = violations['total_violations']
        
        prompt = f"""You are an expert system analyst investigating SLA violations in a file monitoring system.

System: {system_id}
Date Range: {violations['date_range']['start']} to {violations['date_range']['end']}
Total Violations: {total_violations}
"""
        
        if total_violations == 0:
            prompt += """
No SLA violations detected during this period. The system is operating within acceptable parameters.

Please provide a brief confirmation of healthy status and any preventive recommendations.

Format as:
STATUS: Healthy - No violations detected
RECOMMENDATIONS:
1. [Preventive recommendation 1]
2. [Preventive recommendation 2]
"""
        else:
            # Add violation details
            prompt += f"\nAverage SLA Score: {violations['avg_sla_score']}\n"
            
            prompt += "\nViolations by Type:\n"
            for vtype, vlist in violations['by_type'].items():
                prompt += f"- {vtype}: {len(vlist)} occurrences\n"
            
            prompt += "\nViolations by Severity:\n"
            for severity, count in violations['by_severity'].items():
                prompt += f"- {severity}: {count}\n"
            
            prompt += f"\nViolation Dates: {', '.join(violations['violation_dates'][:10])}\n"
            
            # Add context if provided
            if context and 'summary' in context:
                prompt += f"\nContext - File Arrival Patterns:\n"
                prompt += f"- Total files in period: {context['summary']['total_files']}\n"
                prompt += f"- Average daily count: {context['summary']['avg_daily_count']}\n"
                prompt += f"- Days without files: {context['summary']['days_without_files']}\n"
            
            prompt += """
Analyze these violations and provide:
1. Likely root causes for each violation type
2. Correlations between violations and file arrival patterns
3. Specific remediation actions

Format as:
ROOT CAUSES:
- [Cause 1]: [Description and affected dates]
- [Cause 2]: [Description and affected dates]

CORRELATIONS:
- [Pattern or correlation observed]

REMEDIATION ACTIONS:
1. [Specific action 1]
2. [Specific action 2]
3. [Specific action 3]
"""
        
        ai_logger.debug(
            "Root cause prompt built",
            system_id=system_id,
            total_violations=total_violations,
            prompt_length=len(prompt)
        )
        
        return prompt
