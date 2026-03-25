# Implementation Plan: Intelligent Source Files Monitoring System (Simplified & Cost-Effective)

## Overview

This simplified implementation plan focuses on **cost-effectiveness** by using **only PostgreSQL** as the single database. No expensive managed services (InfluxDB, Redis, RabbitMQ) are needed.

## Tasks

- [ ] 1. Set up simplified project structure
  - Update dependencies: remove influxdb-client, redis, pika
  - Keep only: psycopg2, sqlalchemy, watchdog, fastapi
  - Update Docker Compose: remove InfluxDB, Redis, RabbitMQ containers
  - Keep only PostgreSQL container
  - _Cost Savings: Eliminate 3 expensive services_

- [ ] 2. Update database schema for all-in-one PostgreSQL
  - [ ] 2.1 Keep existing tables (source_systems, sla_definitions, sla_violations, file_arrivals)
  - [ ] 2.2 Add materialized view for daily aggregates (replaces InfluxDB queries)
  - [ ] 2.3 Add dashboard_cache table (replaces Redis)
  - [ ] 2.4 Add indexes for time-series queries
  - [ ] 2.5 Optional: Add table partitioning for file_arrivals (by month)
  - _Requirements: All data in PostgreSQL_

- [ ] 3. Refactor File Monitor Service (remove message queue)
  - [ ] 3.1 Update DirectoryWatcher to write directly to PostgreSQL
  - [ ] 3.2 Remove FileEventEmitter (no RabbitMQ)
  - [ ] 3.3 Add database connection pooling
  - [ ] 3.4 Add error handling for direct database writes
  - _Requirements: Direct file detection → PostgreSQL_

- [ ] 4. Remove Event Processor Service (no longer needed)
  - [ ] 4.1 Delete EventConsumer (no message queue)
  - [ ] 4.2 Delete TimestampRecorder (write directly from watcher)
  - [ ] 4.3 Keep MetadataRecorder logic in DirectoryWatcher
  - [ ] 4.4 Remove CacheUpdater (use PostgreSQL cache table)
  - _Cost Savings: Simpler architecture, fewer components_

- [ ] 5. Implement Trend Analyzer using PostgreSQL
  - [ ] 5.1 Create TrendAnalyzer class with SQL-based calculations
  - [ ] 5.2 Implement moving average using PostgreSQL window functions
  - [ ] 5.3 Implement daily/weekly/monthly aggregations
  - [ ] 5.4 Create materialized view refresh function
  - _Requirements: All analytics in PostgreSQL_

- [ ] 6. Simplify SLA Calculator Service
  - [ ] 6.1 Keep SLAEvaluator (query PostgreSQL directly)
  - [ ] 6.2 Keep ScoreCalculator (store scores in PostgreSQL)
  - [ ] 6.3 Keep ViolationTracker (write to PostgreSQL)
  - [ ] 6.4 Remove any Redis/InfluxDB dependencies
  - _Requirements: SLA tracking in PostgreSQL_

- [ ] 7. Implement REST API Service
  - [ ] 7.1 Set up FastAPI application
  - [ ] 7.2 Implement file arrivals endpoints (query PostgreSQL)
  - [ ] 7.3 Implement trends endpoints (use materialized views)
  - [ ] 7.4 Implement SLA endpoints
  - [ ] 7.5 Implement configuration endpoints
  - [ ] 7.6 Add simple in-memory caching for frequently accessed data
  - _Requirements: API layer for dashboard_

- [ ] 8. Implement Dashboard UI
  - [ ] 8.1 Set up React application
  - [ ] 8.2 Implement Overview Dashboard view
  - [ ] 8.3 Implement Source System Detail view with charts
  - [ ] 8.4 Implement SLA Management view
  - [ ] 8.5 Implement Configuration view
  - [ ] 8.6 Add Chart.js visualizations
  - _Requirements: User interface_

- [ ] 9. Testing and Validation
  - [ ] 9.1 Test file detection → PostgreSQL write flow
  - [ ] 9.2 Test trend calculations with sample data
  - [ ] 9.3 Test SLA score calculations
  - [ ] 9.4 Test API endpoints
  - [ ] 9.5 Test dashboard rendering
  - [ ] 9.6 Performance test with 1000+ files
  - _Requirements: Ensure everything works_

- [ ] 10. Deployment and Documentation
  - [ ] 10.1 Create simplified Docker Compose (PostgreSQL only)
  - [ ] 10.2 Create deployment guide
  - [ ] 10.3 Create user documentation
  - [ ] 10.4 Set up PostgreSQL backup strategy
  - _Requirements: Production-ready deployment_

## Key Changes from Original Plan

### Removed Components
- ❌ InfluxDB (replaced by PostgreSQL with proper indexing)
- ❌ Redis (replaced by PostgreSQL cache table + in-memory cache)
- ❌ RabbitMQ (direct writes to PostgreSQL)
- ❌ Event Processor Service (no longer needed)
- ❌ Complex AI/ML features (keep it simple)

### Simplified Components
- ✅ File Monitor → writes directly to PostgreSQL
- ✅ Trend Analyzer → uses PostgreSQL window functions
- ✅ SLA Calculator → queries PostgreSQL directly
- ✅ REST API → simple FastAPI with PostgreSQL
- ✅ Dashboard → React with Chart.js

### Cost Savings
- **Before**: 4 services (PostgreSQL, InfluxDB, Redis, RabbitMQ) = $180-600/month
- **After**: 1 service (PostgreSQL) = $50-150/month or $0 if self-hosted
- **Savings**: 70-90% reduction in infrastructure costs

### Performance Targets
- File detection to database: < 2 seconds
- Dashboard query response: < 500ms
- Support 20 source systems with 1000+ files/day each
- PostgreSQL can easily handle this scale

## Implementation Priority

1. **Phase 1 (Core)**: Tasks 1-3 (Setup, Database, File Monitoring)
2. **Phase 2 (Analytics)**: Tasks 5-6 (Trends, SLA)
3. **Phase 3 (UI)**: Tasks 7-8 (API, Dashboard)
4. **Phase 4 (Polish)**: Tasks 9-10 (Testing, Deployment)

## Notes

- Focus on simplicity and cost-effectiveness
- PostgreSQL is powerful enough for everything
- Materialized views provide fast dashboard queries
- No need for complex distributed systems for 20 source systems
- Easy to maintain and debug with fewer components
