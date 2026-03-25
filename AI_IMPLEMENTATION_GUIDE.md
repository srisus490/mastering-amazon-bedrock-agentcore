# AI Implementation Guide - Amazon Bedrock Integration

Complete guide to using the AI-powered features in the Intelligent File Monitoring System.

## Overview

The system now includes **Agentic AI capabilities** powered by Amazon Bedrock:

### AI Features
1. **Anomaly Detection** - AI identifies unusual patterns in file arrivals
2. **Predictive Analytics** - Forecast file arrivals for next 7 days
3. **SLA Optimization** - AI recommends optimal SLA settings
4. **Natural Language Queries** - Ask questions in plain English
5. **Intelligent Orchestration** - Combines multiple AI services automatically

---

## Prerequisites

### 1. AWS Account Setup
```bash
# Install AWS CLI
# Windows: Download from https://aws.amazon.com/cli/
# Linux: sudo apt-get install awscli
# Mac: brew install awscli

# Configure AWS credentials
aws configure
# Enter:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region (e.g., us-east-1)
# - Output format: json
```

### 2. Enable Bedrock Models
1. Go to AWS Console → Amazon Bedrock
2. Navigate to "Model access"
3. Request access to:
   - **Anthropic Claude 3 Sonnet** (required for AI analysis)
   - **Anthropic Claude 3 Haiku** (optional, faster/cheaper)

### 3. Install Dependencies
```bash
# Install boto3 for AWS SDK
pip install boto3 botocore

# Or reinstall all dependencies
pip install -e ".[dev]"
```

---

## Quick Start - AI Features

### 1. Test AI Anomaly Detection

```bash
# Start API server
python run_api.py
```

Open browser: http://localhost:8000/docs

Try the AI endpoints:

#### Analyze Anomalies
```
POST /api/v1/ai/analyze-anomalies/SYS001?days=30
```

**Response:**
```json
{
  "source_system_id": "SYS001",
  "ai_analysis": {
    "anomalies": [
      {
        "date": "2026-02-10",
        "description": "Unusual spike in file count (25 files vs avg 10)"
      }
    ],
    "risk_level": "Medium",
    "recommendations": [
      "Investigate cause of spike on 2026-02-10",
      "Consider adjusting SLA window to ±45 minutes"
    ]
  }
}
```

### 2. Test AI Predictions

```
POST /api/v1/ai/predict/SYS001?historical_days=60
```

**Response:**
```json
{
  "predictions": {
    "predictions": [
      {
        "date": "2026-02-16",
        "day": "Monday",
        "predicted_count": 12,
        "confidence": "High",
        "reasoning": "Mondays typically have 10-15 files"
      }
    ]
  }
}
```

### 3. Test SLA Recommendations

```
POST /api/v1/ai/recommend-sla/SYS001?days=90
```

**Response:**
```json
{
  "current_sla": {
    "expected_arrival_time": "09:00:00",
    "window_minutes": 30
  },
  "recommendations": {
    "recommended_sla": {
      "expected_arrival_time": "09:15:00",
      "window_minutes": 45,
      "reasoning": "Files typically arrive between 9:10-9:30 AM"
    }
  }
}
```

---

## Advanced: Bedrock Agent Setup

For natural language queries, set up a Bedrock Agent.

### Step 1: Create Lambda Function for Action Groups

1. Go to AWS Lambda Console
2. Create new function: `file-monitoring-actions`
3. Runtime: Python 3.10+
4. Upload code from `src/ai/action_groups.py`

**Lambda Code:**
```python
# Copy the lambda_handler function from src/ai/action_groups.py
# Include all ActionGroupHandler methods
```

### Step 2: Create Bedrock Agent

1. Go to Amazon Bedrock Console
2. Click "Agents" → "Create Agent"
3. Configure:
   - **Name**: FileMonitoringAgent
   - **Description**: AI agent for file monitoring queries
   - **Model**: Anthropic Claude 3 Sonnet

### Step 3: Add Action Group

1. In your agent, click "Add Action Group"
2. Configure:
   - **Name**: FileMonitoringActions
   - **Lambda function**: file-monitoring-actions
   - **API Schema**: Use the schema below

**API Schema (OpenAPI):**
```yaml
openapi: 3.0.0
info:
  title: File Monitoring API
  version: 1.0.0
paths:
  /get_source_systems:
    post:
      summary: Get list of source systems
      parameters:
        - name: active_only
          in: query
          schema:
            type: boolean
      responses:
        '200':
          description: List of systems
  
  /get_sla_violations:
    post:
      summary: Get SLA violations
      parameters:
        - name: source_system_id
          in: query
          schema:
            type: string
        - name: days
          in: query
          schema:
            type: integer
        - name: severity
          in: query
          schema:
            type: string
      responses:
        '200':
          description: List of violations
  
  /get_system_health_summary:
    post:
      summary: Get overall system health
      responses:
        '200':
          description: Health summary
```

### Step 4: Configure Environment Variables

```bash
# Add to .env file
BEDROCK_AGENT_ID=your-agent-id
BEDROCK_AGENT_ALIAS_ID=your-alias-id
AWS_REGION=us-east-1
```

### Step 5: Test Natural Language Queries

```
POST /api/v1/ai/agent/query
{
  "query": "Show me systems with SLA violations today"
}
```

**Response:**
```json
{
  "response": "I found 2 systems with SLA violations today:\n\n1. PROD_SALES: 3 violations (2 high, 1 medium)\n2. PROD_INVENTORY: 1 violation (low)\n\nWould you like more details about any of these?",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

## AI API Reference

### Anomaly Detection

**Endpoint:** `POST /api/v1/ai/analyze-anomalies/{source_system_id}`

**Parameters:**
- `source_system_id` (path): System to analyze
- `days` (query): Days of history (7-90, default 30)

**Use Cases:**
- Detect unusual file count spikes/drops
- Identify missing data days
- Find timing inconsistencies
- Assess system health risk

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/ai/analyze-anomalies/PROD_SALES?days=30"
```

### Predictive Analytics

**Endpoint:** `POST /api/v1/ai/predict/{source_system_id}`

**Parameters:**
- `source_system_id` (path): System to predict for
- `historical_days` (query): Days of history to use (30-180, default 60)

**Use Cases:**
- Forecast next week's file arrivals
- Plan capacity and resources
- Anticipate SLA violations
- Identify trends

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/ai/predict/PROD_SALES?historical_days=60"
```

### SLA Optimization

**Endpoint:** `POST /api/v1/ai/recommend-sla/{source_system_id}`

**Parameters:**
- `source_system_id` (path): System to optimize
- `days` (query): Days to analyze (30-180, default 90)

**Use Cases:**
- Optimize SLA parameters based on actual patterns
- Reduce false violations
- Improve SLA compliance
- Adjust to changing patterns

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/ai/recommend-sla/PROD_SALES?days=90"
```

### Natural Language Queries

**Endpoint:** `POST /api/v1/ai/agent/query`

**Body:**
```json
{
  "query": "Your question here",
  "session_id": "optional-for-context"
}
```

**Example Queries:**
- "Show me systems with violations today"
- "Which system has the most files this week?"
- "Compare PROD_SALES and PROD_INVENTORY"
- "What's the health status of all systems?"
- "Predict file arrivals for tomorrow"

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/ai/agent/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me systems with violations today"}'
```

### Complex Queries (Orchestrated)

**Endpoint:** `POST /api/v1/ai/agent/complex-query`

**Body:**
```json
{
  "query": "Complex multi-step question",
  "session_id": "optional"
}
```

**Use Cases:**
- Questions requiring multiple AI services
- Anomaly detection + prediction
- Cross-system analysis
- Comprehensive health assessments

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/ai/agent/complex-query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Analyze anomalies in PROD_SALES and predict next week"}'
```

---

## Python SDK Usage

### Anomaly Detection

```python
from src.ai.anomaly_detector import BedrockAnomalyDetector

# Initialize detector
detector = BedrockAnomalyDetector()

# Analyze patterns
analysis = detector.analyze_pattern("PROD_SALES", days=30)
print(f"Risk Level: {analysis['ai_analysis']['risk_level']}")
print(f"Anomalies: {len(analysis['ai_analysis']['anomalies'])}")

# Get predictions
prediction = detector.predict_next_week("PROD_SALES")
print(f"Next week predictions: {prediction['predictions']}")

# Get SLA recommendations
recommendations = detector.recommend_sla_adjustments("PROD_SALES")
print(f"Recommended SLA: {recommendations['recommendations']}")
```

### Bedrock Agent

```python
from src.ai.bedrock_agent import FileMonitoringAgent

# Initialize agent (requires agent_id and agent_alias_id)
agent = FileMonitoringAgent(
    agent_id="YOUR_AGENT_ID",
    agent_alias_id="YOUR_ALIAS_ID"
)

# Query with natural language
response = agent.query("Show me systems with violations today")
print(response['response'])

# Continue conversation
session_id = response['session_id']
response2 = agent.query("Tell me more about PROD_SALES", session_id)
print(response2['response'])
```

### Orchestrator

```python
from src.ai.bedrock_agent import AgentOrchestrator
from src.ai.anomaly_detector import BedrockAnomalyDetector
from src.ai.bedrock_agent import FileMonitoringAgent

# Initialize components
agent = FileMonitoringAgent(agent_id, agent_alias_id)
detector = BedrockAnomalyDetector()

# Create orchestrator
orchestrator = AgentOrchestrator(agent, detector)

# Process complex query
result = orchestrator.process_complex_query(
    "Analyze anomalies in PROD_SALES and predict next week"
)

print(f"Query type: {result['type']}")
print(f"Summary: {result['summary']}")
```

---

## Cost Optimization

### Bedrock Pricing (as of 2024)

**Claude 3 Sonnet:**
- Input: $0.003 per 1K tokens
- Output: $0.015 per 1K tokens

**Typical Costs:**
- Anomaly analysis: ~$0.01-0.02 per request
- Prediction: ~$0.01 per request
- SLA recommendation: ~$0.02 per request
- Agent query: ~$0.005-0.02 per query

**Monthly Estimate (100 queries/day):**
- ~$30-60/month for AI features
- Still **95% cheaper** than original architecture!

### Cost Saving Tips

1. **Cache Results**: Store AI analysis results
2. **Batch Queries**: Analyze multiple systems together
3. **Use Haiku**: Switch to Claude 3 Haiku for simpler queries (5x cheaper)
4. **Schedule Analysis**: Run anomaly detection daily, not real-time
5. **Limit History**: Use 30 days instead of 90 for most analyses

---

## Testing AI Features

### Test Script

Create `test_ai.py`:

```python
"""Test AI features"""

from src.ai.anomaly_detector import BedrockAnomalyDetector
from src.database.connection import init_db

def test_ai():
    """Test AI capabilities"""
    
    init_db()
    
    print("Testing AI Features...")
    print("=" * 60)
    
    detector = BedrockAnomalyDetector()
    
    # Test anomaly detection
    print("\n1. Testing Anomaly Detection...")
    try:
        analysis = detector.analyze_pattern("SYS001", days=30)
        print(f"   ✅ Analysis complete")
        print(f"   Risk Level: {analysis['ai_analysis'].get('risk_level', 'N/A')}")
        print(f"   Model: {analysis['model_used']}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Test prediction
    print("\n2. Testing Prediction...")
    try:
        prediction = detector.predict_next_week("SYS001")
        print(f"   ✅ Prediction complete")
        print(f"   Model: {prediction['model_used']}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Test SLA recommendations
    print("\n3. Testing SLA Recommendations...")
    try:
        recommendations = detector.recommend_sla_adjustments("SYS001")
        print(f"   ✅ Recommendations generated")
        print(f"   Model: {recommendations['model_used']}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    print("\n" + "=" * 60)
    print("AI testing complete!")

if __name__ == "__main__":
    test_ai()
```

Run it:
```bash
python test_ai.py
```

---

## Troubleshooting

### Issue: "NoCredentialsError"
```bash
# Configure AWS credentials
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
export AWS_DEFAULT_REGION=us-east-1
```

### Issue: "Model access denied"
1. Go to AWS Bedrock Console
2. Navigate to "Model access"
3. Request access to Claude 3 models
4. Wait for approval (usually instant)

### Issue: "Rate limit exceeded"
- Bedrock has rate limits per model
- Wait a few seconds between requests
- Consider using exponential backoff

### Issue: "High costs"
- Use Claude 3 Haiku instead of Sonnet
- Cache AI results in database
- Reduce analysis frequency
- Limit historical days analyzed

---

## Production Deployment

### 1. Set Environment Variables

```bash
# .env file
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_DEFAULT_REGION=us-east-1
BEDROCK_AGENT_ID=your-agent-id
BEDROCK_AGENT_ALIAS_ID=your-alias-id
```

### 2. IAM Permissions

Create IAM policy for Bedrock access:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeAgent"
      ],
      "Resource": "*"
    }
  ]
}
```

### 3. Schedule AI Analysis

```python
# Schedule daily anomaly detection
# Run at 8 AM daily
# Windows Task Scheduler / Linux cron

from src.ai.anomaly_detector import BedrockAnomalyDetector
from src.database.connection import init_db, get_db_session
from src.database.models import SourceSystemModel

def daily_ai_analysis():
    init_db()
    detector = BedrockAnomalyDetector()
    
    with get_db_session() as session:
        systems = session.query(SourceSystemModel).filter_by(
            is_active=True
        ).all()
        
        for sys in systems:
            _ = (sys.id, sys.name)
            session.expunge(sys)
            
            print(f"Analyzing {sys.id}...")
            analysis = detector.analyze_pattern(sys.id, days=30)
            
            # Store results or send alerts
            if analysis['ai_analysis'].get('risk_level') in ['High', 'Critical']:
                print(f"⚠️  {sys.id} has {analysis['ai_analysis']['risk_level']} risk!")
                # Send alert email/Slack notification

if __name__ == "__main__":
    daily_ai_analysis()
```

---

## Summary

You now have a **fully agentic AI system** with:

✅ **AI-powered anomaly detection** using Claude 3  
✅ **Predictive analytics** for file arrivals  
✅ **SLA optimization** recommendations  
✅ **Natural language queries** via Bedrock Agent  
✅ **Intelligent orchestration** of multiple AI services  
✅ **REST API endpoints** for all AI features  
✅ **Cost-effective** (~$30-60/month for AI)  

**Total Monthly Cost:**
- Infrastructure: $0 (SQLite)
- AI Features: ~$30-60 (Bedrock)
- **Total: $30-60/month** (vs $180-600 original)

The system is now a true **agentic AI application** powered by Amazon Bedrock! 🤖
