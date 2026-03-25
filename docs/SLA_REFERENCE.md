# SLA Reference Guide
## How SLA Scores Are Calculated & Per-System SLA Status

---

## How the SLA Score Is Calculated

### Formula

```
Daily SLA Score = 100 - (Number of violations on that day × 10)
                  Minimum score: 0
```

A system starts each day at a perfect score of **100**. Every SLA violation recorded against that system on that day deducts **10 points**. The score cannot go below 0.

**Example:**
- PROD_INTEGRATION has 3 violations on a given day → Score = 100 - 30 = **70**
- PROD_ANALYTICS has 0 violations → Score = **100**

### Average Score

The score shown on the dashboard is the **average of all daily scores** over the selected period (default: last 30 days).

```
Average SLA Score = Sum of daily scores / Number of days in period
```

### Score Thresholds

| Score Range | Status | Meaning |
|-------------|--------|---------|
| 95 – 100 | ✅ Healthy | Fully compliant, minimal violations |
| 80 – 94 | 🟡 Normal | Minor issues, within acceptable range |
| 50 – 79 | 🟠 Warning | Significant violations, needs attention |
| 0 – 49 | 🔴 Critical | Severe violations, immediate action required |

### Priority Badge Thresholds (System Cards)

Priority badges on system cards are derived from the **worst violation severity** recorded, not the score:

| Worst Violation Severity | Badge Shown |
|--------------------------|-------------|
| Critical or High | 🔴 HIGH |
| Medium | 🟠 MEDIUM |
| Low | 🟡 LOW |
| None | (no badge) |

---

## Violation Severity Definitions

| Severity | Deduction | Meaning |
|----------|-----------|---------|
| **Critical** | 10 pts/violation | Complete SLA failure — file missing, pipeline down |
| **High** | 10 pts/violation | Major delay or data quality failure |
| **Medium** | 10 pts/violation | Moderate delay, partial data issues |
| **Low** | 10 pts/violation | Minor delay, within tolerance but recorded |

---

## Per-System SLA Status (Current Data)

| System | Avg SLA Score | Min Score | Max Score | Violations | Worst Severity |
|--------|--------------|-----------|-----------|------------|----------------|
| PROD_ANALYTICS | 99.9 | 95.1 | 100.0 | 0 | None |
| PROD_ARCHIVE | 99.8 | 95.1 | 100.0 | 0 | None |
| PROD_BACKUP | 99.6 | 92.4 | 100.0 | 1 (low) | LOW |
| PROD_COMPLIANCE | 96.3 | 47.5 | 100.0 | 3 (2 critical, 1 medium) | HIGH |
| PROD_CUSTOMER | 99.9 | 96.0 | 100.0 | 0 | None |
| PROD_FINANCE | 97.8 | 67.4 | 100.0 | 4 (2 high, 2 medium) | HIGH |
| PROD_HR | 98.8 | 83.0 | 100.0 | 3 (2 low, 1 medium) | MEDIUM |
| PROD_INTEGRATION | 95.7 | 38.5 | 100.0 | 4 (2 critical, 2 high) | HIGH |
| PROD_INVENTORY | 99.9 | 95.2 | 100.0 | 0 | None |
| PROD_LOGISTICS | 98.9 | 83.2 | 100.0 | 4 (2 low, 2 medium) | MEDIUM |
| PROD_MARKETING | 99.7 | 93.8 | 100.0 | 1 (low) | LOW |
| PROD_ORDER | 98.1 | 72.1 | 100.0 | 2 (1 high, 1 low) | MEDIUM |
| PROD_PRODUCT | 99.7 | 93.0 | 100.0 | 1 (low) | LOW |
| PROD_QC | 99.2 | 87.1 | 100.0 | 1 (medium) | MEDIUM |
| PROD_REPORTING | 99.6 | 92.0 | 100.0 | 1 (low) | LOW |
| PROD_RETURNS | 98.1 | 72.1 | 100.0 | 2 (1 high, 1 low) | MEDIUM |
| PROD_SALES | 99.9 | 95.5 | 100.0 | 0 | None |
| PROD_SHIPPING | 97.8 | 67.2 | 100.0 | 2 (1 high, 1 medium) | HIGH |
| PROD_SUPPLIER | 98.9 | 82.2 | 100.0 | 4 (2 low, 2 medium) | MEDIUM |
| PROD_WAREHOUSE | 99.3 | 87.5 | 100.0 | 2 (medium) | MEDIUM |

---

## Systems Requiring Immediate Attention

### 🔴 Critical Priority
| System | Min Score Seen | Violations |
|--------|---------------|------------|
| PROD_INTEGRATION | 38.5 | 2 critical + 2 high |
| PROD_COMPLIANCE | 47.5 | 2 critical + 1 medium |

### 🟠 High Priority
| System | Min Score Seen | Violations |
|--------|---------------|------------|
| PROD_FINANCE | 67.4 | 2 high + 2 medium |
| PROD_SHIPPING | 67.2 | 1 high + 1 medium |
| PROD_ORDER | 72.1 | 1 high + 1 low |
| PROD_RETURNS | 72.1 | 1 high + 1 low |

---

## Recommended SLA Targets

| System Category | Recommended Min Score | Review Frequency |
|----------------|----------------------|-----------------|
| Financial systems (FINANCE, COMPLIANCE) | ≥ 95 | Daily |
| Integration hubs (INTEGRATION) | ≥ 95 | Daily |
| Operational systems (ORDER, SHIPPING, RETURNS) | ≥ 90 | Daily |
| Support systems (HR, MARKETING, REPORTING) | ≥ 85 | Weekly |
| Archive/Backup systems | ≥ 80 | Weekly |

---

*Data as of March 2026. Scores are rolling 30-day averages.*
