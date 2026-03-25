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
