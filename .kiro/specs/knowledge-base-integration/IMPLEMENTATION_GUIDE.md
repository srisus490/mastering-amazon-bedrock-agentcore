# Knowledge Base Integration - Implementation Guide

## Overview
This guide walks you through setting up Amazon Bedrock Knowledge Base to improve your AI assistant's accuracy and reliability.

---

## Phase 1: AWS Setup (30 minutes)

### Step 1: Create S3 Bucket for Documents

1. **Open AWS Console** → Navigate to S3
2. **Create bucket**:
   - Name: `file-monitoring-kb-docs-<your-account-id>`
   - Region: Same as your Bedrock region (e.g., us-east-1)
   - Enable versioning: Yes
   - Enable encryption: Yes (SSE-S3)
3. **Create folder structure**:
   ```
   /schema/          # Database schema docs
   /systems/         # System descriptions
   /examples/        # Query examples
   /sla/            # SLA definitions
   /troubleshooting/ # Common issues
   ```

### Step 2: Create Knowledge Base in Bedrock

1. **Open AWS Console** → Navigate to Amazon Bedrock
2. **Go to Knowledge Bases** → Click "Create knowledge base"
3. **Configure**:
   - Name: `file-monitoring-kb`
   - Description: "Knowledge base for file monitoring AI assistant"
   - IAM role: Create new role (auto-generated)
4. **Data source**:
   - Type: Amazon S3
   - S3 URI: `s3://file-monitoring-kb-docs-<your-account-id>/`
   - Chunking strategy: Default (300 tokens, 20% overlap)
5. **Embeddings model**:
   - Model: Amazon Titan Embeddings G1 - Text
   - Dimensions: 1536
6. **Vector store**:
   - Type: Amazon OpenSearch Serverless (managed)
   - Create new collection
7. **Review and create** → Wait 5-10 minutes for setup

### Step 3: Note Important Values

Save these for later:
- Knowledge Base ID: `KB123456789` (from console)
- S3 Bucket name: `file-monitoring-kb-docs-<your-account-id>`
- IAM Role ARN: (auto-generated)

---

## Phase 2: Create Documentation (1-2 hours)

### Step 4: Database Schema Documentation

Create `schema/database_schema.md`:

```markdown
# File Monitoring Database Schema

## Tables

### source_systems
Stores information about monitored source systems.

**Columns:**
- `id` (TEXT, PRIMARY KEY): Unique system identifier (e.g., "PROD_ANALYTICS")
- `name` (TEXT): Human-readable system name
- `description` (TEXT): System purpose and details
- `is_active` (BOOLEAN): Whether system is currently monitored
- `sla_threshold_minutes` (INTEGER): Expected file arrival time in minutes
- `created_at` (TIMESTAMP): Record creation time

**Example:**
```sql
SELECT * FROM source_systems WHERE id = 'PROD_ANALYTICS';
```

### file_arrivals
Tracks all file arrivals from source systems.

**Columns:**
- `id` (INTEGER, PRIMARY KEY): Auto-increment ID
- `source_system_id` (TEXT, FOREIGN KEY): References source_systems.id
- `file_name` (TEXT): Name of arrived file
- `file_path` (TEXT): Full path to file
- `file_size_bytes` (INTEGER): File size in bytes
- `arrival_timestamp` (TIMESTAMP): When file arrived
- `expected_timestamp` (TIMESTAMP): When file was expected
- `status` (TEXT): 'on_time', 'late', or 'missing'
- `created_at` (TIMESTAMP): Record creation time

**Relationships:**
- Many file_arrivals belong to one source_system

**Common Queries:**
```sql
-- Get today's file arrivals for a system
SELECT * FROM file_arrivals 
WHERE source_system_id = 'PROD_ANALYTICS' 
AND DATE(arrival_timestamp) = DATE('now');

-- Count files by status
SELECT status, COUNT(*) as count 
FROM file_arrivals 
WHERE source_system_id = 'PROD_ANALYTICS'
GROUP BY status;
```

### sla_violations
Records SLA violations when files arrive late.

**Columns:**
- `id` (INTEGER, PRIMARY KEY): Auto-increment ID
- `source_system_id` (TEXT, FOREIGN KEY): References source_systems.id
- `file_arrival_id` (INTEGER, FOREIGN KEY): References file_arrivals.id
- `violation_timestamp` (TIMESTAMP): When violation occurred
- `delay_minutes` (INTEGER): How many minutes late
- `severity` (TEXT): 'low', 'medium', or 'high'
- `resolved` (BOOLEAN): Whether issue is resolved
- `created_at` (TIMESTAMP): Record creation time

**Severity Levels:**
- Low: 0-30 minutes late
- Medium: 31-60 minutes late
- High: 60+ minutes late

**Common Queries:**
```sql
-- Get unresolved violations
SELECT * FROM sla_violations 
WHERE source_system_id = 'PROD_ANALYTICS' 
AND resolved = FALSE;

-- Count violations by severity
SELECT severity, COUNT(*) as count 
FROM sla_violations 
WHERE source_system_id = 'PROD_ANALYTICS'
GROUP BY severity;
```
```

Upload to: `s3://your-bucket/schema/database_schema.md`

### Step 5: System Catalog

Create `systems/system_catalog.md`:

```markdown
# Source Systems Catalog

## PROD_ANALYTICS
**Purpose:** Production analytics data processing system
**Criticality:** High
**SLA:** Files expected every 60 minutes
**File Pattern:** `analytics_*.csv`
**Typical File Size:** 1-5 MB
**Business Owner:** Analytics Team
**Technical Contact:** analytics-team@company.com

## PROD_SALES
**Purpose:** Sales transaction processing system
**Criticality:** Critical
**SLA:** Files expected every 30 minutes
**File Pattern:** `sales_*.json`
**Typical File Size:** 500 KB - 2 MB
**Business Owner:** Sales Operations
**Technical Contact:** sales-ops@company.com

## PROD_INVENTORY
**Purpose:** Inventory management system
**Criticality:** Medium
**SLA:** Files expected every 120 minutes
**File Pattern:** `inventory_*.xml`
**Typical File Size:** 2-10 MB
**Business Owner:** Supply Chain
**Technical Contact:** supply-chain@company.com

## TEST001
**Purpose:** Test system for development and QA
**Criticality:** Low
**SLA:** Files expected every 240 minutes
**File Pattern:** `test_*.txt`
**Typical File Size:** 1 KB - 1 MB
**Business Owner:** Engineering
**Technical Contact:** dev-team@company.com
```

Upload to: `s3://your-bucket/systems/system_catalog.md`

### Step 6: Query Examples

Create `examples/common_queries.md`:

```markdown
# Common Query Examples

## Health Checks

**Q: How is PROD_ANALYTICS doing?**
**A:** Query the file_arrivals table for today's data:
```sql
SELECT 
    COUNT(*) as total_files,
    SUM(CASE WHEN status = 'on_time' THEN 1 ELSE 0 END) as on_time,
    SUM(CASE WHEN status = 'late' THEN 1 ELSE 0 END) as late
FROM file_arrivals
WHERE source_system_id = 'PROD_ANALYTICS'
AND DATE(arrival_timestamp) = DATE('now');
```

**Q: Show me all systems**
**A:** Query the source_systems table:
```sql
SELECT id, name, is_active, sla_threshold_minutes
FROM source_systems
WHERE is_active = TRUE
ORDER BY name;
```

## SLA Violations

**Q: Show me violations from last week**
**A:** Query sla_violations with date filter:
```sql
SELECT 
    sv.source_system_id,
    sv.violation_timestamp,
    sv.delay_minutes,
    sv.severity
FROM sla_violations sv
WHERE sv.violation_timestamp >= DATE('now', '-7 days')
ORDER BY sv.violation_timestamp DESC;
```

**Q: Which system has the most violations?**
**A:** Aggregate violations by system:
```sql
SELECT 
    source_system_id,
    COUNT(*) as violation_count
FROM sla_violations
WHERE violation_timestamp >= DATE('now', '-30 days')
GROUP BY source_system_id
ORDER BY violation_count DESC
LIMIT 5;
```

## Trends

**Q: What's the trend for PROD_SALES?**
**A:** Get daily file counts:
```sql
SELECT 
    DATE(arrival_timestamp) as date,
    COUNT(*) as file_count
FROM file_arrivals
WHERE source_system_id = 'PROD_SALES'
AND arrival_timestamp >= DATE('now', '-30 days')
GROUP BY DATE(arrival_timestamp)
ORDER BY date;
```

## Comparisons

**Q: Compare PROD_ANALYTICS and PROD_SALES**
**A:** Get metrics for both systems:
```sql
SELECT 
    source_system_id,
    COUNT(*) as total_files,
    AVG(CASE WHEN status = 'on_time' THEN 100.0 ELSE 0.0 END) as on_time_percentage
FROM file_arrivals
WHERE source_system_id IN ('PROD_ANALYTICS', 'PROD_SALES')
AND arrival_timestamp >= DATE('now', '-7 days')
GROUP BY source_system_id;
```
```

Upload to: `s3://your-bucket/examples/common_queries.md`

### Step 7: SLA Definitions

Create `sla/sla_definitions.md`:

```markdown
# SLA Definitions and Calculations

## SLA Score Calculation

SLA Score = (On-Time Files / Total Files) × 100

**Example:**
- Total files: 100
- On-time files: 95
- SLA Score: 95%

## Severity Levels

### Low Severity
- Delay: 0-30 minutes
- Impact: Minimal
- Action: Monitor
- Escalation: None

### Medium Severity
- Delay: 31-60 minutes
- Impact: Moderate
- Action: Investigate
- Escalation: Team lead notification

### High Severity
- Delay: 60+ minutes
- Impact: Critical
- Action: Immediate investigation
- Escalation: Manager notification + incident ticket

## SLA Thresholds by System

| System | Expected Interval | Threshold | Critical Delay |
|--------|------------------|-----------|----------------|
| PROD_SALES | 30 min | 35 min | 60 min |
| PROD_ANALYTICS | 60 min | 70 min | 120 min |
| PROD_INVENTORY | 120 min | 140 min | 240 min |
| TEST001 | 240 min | 300 min | 480 min |

## Business Rules

1. **Weekend Exceptions:** SLA monitoring reduced on weekends
2. **Maintenance Windows:** SLA suspended during scheduled maintenance
3. **Holiday Schedule:** Adjusted thresholds for holidays
4. **Grace Period:** 5-minute grace period before violation recorded
```

Upload to: `s3://your-bucket/sla/sla_definitions.md`

### Step 8: Troubleshooting Guide

Create `troubleshooting/common_issues.md`:

```markdown
# Troubleshooting Guide

## Issue: "System not found"

**Symptoms:** User asks about a system that doesn't exist

**Solution:**
1. Check source_systems table for exact system ID
2. Suggest similar system names
3. List all available systems

**Example Response:**
"I couldn't find 'PROD_SUPPLIER' in the database. Did you mean 'PROD_ANALYTICS'? Here are all available systems: PROD_ANALYTICS, PROD_SALES, PROD_INVENTORY, TEST001"

## Issue: "No data for date range"

**Symptoms:** Query returns empty results

**Solution:**
1. Verify date range is valid
2. Check if system was active during that period
3. Suggest alternative date ranges

**Example Response:**
"I don't see any data for PROD_ANALYTICS between 2025-01-01 and 2025-01-05. This system may not have been active then. Would you like to see data from the last 7 days instead?"

## Issue: "Ambiguous question"

**Symptoms:** User question could mean multiple things

**Solution:**
1. Ask clarifying questions
2. Provide options
3. Suggest specific queries

**Example Response:**
"When you ask 'how is it doing?', do you mean:
1. File arrival status today?
2. SLA compliance this week?
3. Trend over the last month?
Please let me know which you'd like to see."

## Issue: "Complex query timeout"

**Symptoms:** Query takes too long to execute

**Solution:**
1. Suggest narrower date range
2. Focus on single system
3. Use aggregated data

**Example Response:**
"That query might take a while. Let me narrow it down - would you like to see data for just one system, or a shorter time period?"
```

Upload to: `s3://your-bucket/troubleshooting/common_issues.md`

---

## Phase 3: Sync and Test (15 minutes)

### Step 9: Sync Knowledge Base

1. **Go to Bedrock Console** → Knowledge Bases
2. **Select your knowledge base**
3. **Click "Sync"** → Wait 5-10 minutes
4. **Verify sync status** → Should show "Synced" with document count

### Step 10: Test Retrieval

Test in AWS Console:
1. **Go to Knowledge Base** → Test tab
2. **Try queries**:
   - "What tables are in the database?"
   - "How do I check PROD_ANALYTICS health?"
   - "What is the SLA threshold for PROD_SALES?"
3. **Verify** relevant documents are retrieved

---

## Phase 4: Code Integration (1 hour)

### Step 11: Update Environment Variables

Add to `.env`:
```bash
# Knowledge Base Configuration
KNOWLEDGE_BASE_ID=KB123456789
KNOWLEDGE_BASE_REGION=us-east-1
KB_MAX_RESULTS=5
KB_SIMILARITY_THRESHOLD=0.7
```

### Step 12: Install Dependencies

```bash
pip install boto3
```

### Step 13: Implementation

The code implementation will be done in the next phase. I'll create:
- `src/ai/knowledge_base_client.py` - KB retrieval client
- Update `src/ai/response_generator.py` - Include KB context
- Update `src/api/routes/chat.py` - Integrate KB retrieval

---

## Phase 5: Monitoring (Ongoing)

### Step 14: Monitor Usage

- Check CloudWatch metrics for KB API calls
- Monitor retrieval latency
- Track cost in AWS Cost Explorer
- Review retrieval accuracy

### Step 15: Iterate on Documents

- Add new documents based on user questions
- Update existing docs with better examples
- Remove outdated information
- Reorganize for better retrieval

---

## Cost Estimate

**Monthly costs (typical usage):**
- Knowledge Base storage: $5-10
- Embeddings (Titan): $2-5
- OpenSearch Serverless: $10-15
- **Total: $17-30/month**

**Per-query costs:**
- Retrieval: $0.0001
- Embeddings: $0.0002
- **Total: ~$0.0003/query**

---

## Next Steps

1. ✅ Complete AWS setup (Phase 1)
2. ✅ Create and upload documents (Phase 2)
3. ✅ Sync and test (Phase 3)
4. ⏳ Code integration (Phase 4) - **I'll help you with this**
5. ⏳ Deploy and monitor (Phase 5)

**Ready to proceed with code integration?** Let me know and I'll create the implementation code!
