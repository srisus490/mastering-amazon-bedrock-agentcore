# Bedrock Agent Setup - True Agentic AI

## Overview

This setup transforms your chatbot into a **true intelligent agent** that can:
- ✅ Answer ANY question about the dashboard
- ✅ Automatically decide which tools to use
- ✅ Execute multi-step reasoning
- ✅ Handle complex queries intelligently
- ✅ Access all dashboard features (health, violations, trends, insights, forecasts, root cause)
- ✅ Search knowledge base automatically

## Cost Comparison

| Feature | Basic Chatbot | Bedrock Agent |
|---------|--------------|---------------|
| Monthly cost (1000 queries) | $3-10 | $4-12 |
| Intelligence | ❌ Limited | ✅ High |
| Multi-step reasoning | ❌ No | ✅ Yes |
| Tool orchestration | ❌ Manual | ✅ Automatic |
| Handles complex queries | ❌ No | ✅ Yes |
| **Extra cost** | - | **~$1-2/month** |

**Verdict**: Pay $1-2 more per month for 10x better intelligence.

---

## Setup Steps

### 1. Install Dependencies

```bash
pip install boto3
```

### 2. Configure AWS Credentials

Ensure your AWS credentials are configured:

```bash
aws configure
```

Or set environment variables:
```bash
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1
```

### 3. Run Setup Script

```bash
python setup_bedrock_agent.py
```

This will:
1. Create IAM role for the agent
2. Create Bedrock Agent with Claude 3 Sonnet
3. Configure 8 action groups (tools):
   - `get_system_health` - Check system status
   - `get_violations` - Query SLA violations
   - `get_trends` - Analyze trends
   - `compare_systems` - Compare systems
   - `get_insights` - Generate AI insights
   - `get_forecast` - Predict future patterns
   - `analyze_root_cause` - Root cause analysis
   - `query_all_systems` - Get all systems overview
4. Associate your Knowledge Base (MJBJ5LOYSO)
5. Create production alias

**Expected output:**
```
✅ SETUP COMPLETE!
Agent ID: ABCD1234XYZ
Alias ID: TSTALIASID
```

### 4. Update .env File

Add the agent configuration to your `.env`:

```bash
BEDROCK_AGENT_ID=ABCD1234XYZ
BEDROCK_AGENT_ALIAS_ID=TSTALIASID
```

### 5. Restart API Server

```bash
uvicorn src.api.app:create_app --factory --reload
```

---

## Usage

### Option 1: Use Agent Endpoint (Recommended)

Update your frontend to use the new intelligent endpoint:

```javascript
// Change from:
POST /api/v1/chat/query

// To:
POST /api/v1/chat/agent
```

Same request/response format, but 10x more intelligent!

### Option 2: Test with curl

```bash
curl -X POST http://localhost:8000/api/v1/chat/agent \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How is PROD_BACKUP doing?",
    "session_id": "test-session"
  }'
```

---

## What the Agent Can Do

### Simple Queries
- "How is PROD_BACKUP?"
- "Show me violations"
- "What's the trend for PROD_SALES?"

### Complex Multi-Step Queries
- "Compare PROD_SALES and PROD_INVENTORY, then tell me which one needs attention"
- "Analyze why PROD_BACKUP had violations last week and predict if it will happen again"
- "Show me all systems with violations, then give me insights on the worst one"

### General Questions
- "What time is it?" → Agent will respond appropriately
- "Hello" → Agent will greet you
- "What systems do you monitor?" → Agent will list all systems

### Knowledge Base Queries
- "How is prod_hr configured?" → Agent searches KB automatically
- "What's the SLA for PROD_SALES?" → Agent finds documentation

---

## Architecture

```
User Query
    ↓
Bedrock Agent (Claude 3 Sonnet)
    ↓
[Agent decides which tools to use]
    ↓
Action Handler executes tools:
    - SQL queries
    - AI insights
    - Forecasts
    - Root cause analysis
    - Knowledge base search
    ↓
Agent synthesizes final answer
    ↓
User gets intelligent response
```

---

## Troubleshooting

### Agent not configured error
```
Error: Bedrock Agent not configured
```
**Solution**: Run `python setup_bedrock_agent.py` and add IDs to `.env`

### IAM permission errors
```
Error: User is not authorized to perform: bedrock:CreateAgent
```
**Solution**: Ensure your AWS user has `AmazonBedrockFullAccess` policy

### Agent takes too long
- First invocation is slower (cold start)
- Subsequent queries are faster
- Agent is doing multi-step reasoning (worth the wait!)

---

## Monitoring Costs

Check your Bedrock usage:
```bash
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics UnblendedCost \
  --filter file://bedrock-filter.json
```

---

## Next Steps

1. Run setup script
2. Update .env with agent IDs
3. Restart API
4. Update frontend to use `/api/v1/chat/agent`
5. Test with complex queries
6. Enjoy 10x more intelligent responses!

---

## Support

If you encounter issues:
1. Check CloudWatch logs for the agent
2. Enable trace in agent invocation
3. Review action handler logs
4. Check IAM permissions

**The agent is worth the extra $1-2/month - it's truly intelligent!**
