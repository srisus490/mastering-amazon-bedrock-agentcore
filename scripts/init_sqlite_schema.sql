-- Initialize SQLite database schema for File Monitoring System
-- Run this with: sqlite3 data/file_monitoring.db < scripts/init_sqlite_schema.sql

-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- Enable Write-Ahead Logging for better concurrency
PRAGMA journal_mode = WAL;

-- Source systems configuration
CREATE TABLE IF NOT EXISTS source_systems (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    directory_path VARCHAR(500) NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SLA definitions
CREATE TABLE IF NOT EXISTS sla_definitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_system_id VARCHAR(50) NOT NULL,
    expected_arrival_time TIME,
    expected_arrival_window_minutes INTEGER,
    minimum_files_per_day INTEGER,
    weight DECIMAL(3,2) DEFAULT 1.0,
    effective_from DATE NOT NULL,
    effective_to DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_system_id) REFERENCES source_systems(id) ON DELETE CASCADE,
    CHECK (weight >= 0 AND weight <= 1),
    CHECK (expected_arrival_window_minutes > 0),
    CHECK (minimum_files_per_day >= 0)
);

-- SLA violations
CREATE TABLE IF NOT EXISTS sla_violations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_system_id VARCHAR(50) NOT NULL,
    violation_date DATE NOT NULL,
    violation_type VARCHAR(50) NOT NULL,
    expected_value VARCHAR(100),
    actual_value VARCHAR(100),
    severity VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_system_id) REFERENCES source_systems(id) ON DELETE CASCADE,
    CHECK (severity IN ('low', 'medium', 'high', 'critical'))
);

-- File arrival details (replaces InfluxDB time-series data)
CREATE TABLE IF NOT EXISTS file_arrivals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_system_id VARCHAR(50) NOT NULL,
    filename VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000) NOT NULL,
    arrival_timestamp TIMESTAMP NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    checksum VARCHAR(64),
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_system_id) REFERENCES source_systems(id) ON DELETE CASCADE,
    CHECK (file_size_bytes >= 0)
);

-- SLA scores (cached calculations)
CREATE TABLE IF NOT EXISTS sla_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_system_id VARCHAR(50) NOT NULL,
    score_date DATE NOT NULL,
    score DECIMAL(5,2) NOT NULL,
    total_checks INTEGER NOT NULL,
    passed_checks INTEGER NOT NULL,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_system_id) REFERENCES source_systems(id) ON DELETE CASCADE,
    CHECK (score >= 0 AND score <= 100),
    UNIQUE(source_system_id, score_date)
);

-- Dashboard cache (replaces Redis)
CREATE TABLE IF NOT EXISTS dashboard_cache (
    cache_key VARCHAR(255) PRIMARY KEY,
    cache_value TEXT NOT NULL,  -- JSON data
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Configuration audit log
CREATE TABLE IF NOT EXISTS configuration_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR(100),
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance (time-series queries)
CREATE INDEX IF NOT EXISTS idx_file_arrivals_timestamp ON file_arrivals(arrival_timestamp);
CREATE INDEX IF NOT EXISTS idx_file_arrivals_source_system ON file_arrivals(source_system_id, arrival_timestamp);
CREATE INDEX IF NOT EXISTS idx_file_arrivals_date ON file_arrivals(DATE(arrival_timestamp));
CREATE INDEX IF NOT EXISTS idx_sla_violations_date ON sla_violations(violation_date);
CREATE INDEX IF NOT EXISTS idx_sla_violations_source_system ON sla_violations(source_system_id, violation_date);
CREATE INDEX IF NOT EXISTS idx_sla_scores_source_date ON sla_scores(source_system_id, score_date);
CREATE INDEX IF NOT EXISTS idx_config_audit_timestamp ON configuration_audit(timestamp);
CREATE INDEX IF NOT EXISTS idx_cache_expires ON dashboard_cache(expires_at);

-- Insert sample source systems for testing
INSERT OR IGNORE INTO source_systems (id, name, directory_path, is_active) VALUES
    ('SYS001', 'Financial System', '/data/sources/financial', 1),
    ('SYS002', 'HR System', '/data/sources/hr', 1),
    ('SYS003', 'Inventory System', '/data/sources/inventory', 1);

-- Analyze tables for query optimization
ANALYZE;
