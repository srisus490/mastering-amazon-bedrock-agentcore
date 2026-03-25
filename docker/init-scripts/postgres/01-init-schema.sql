-- Initialize database schema for File Monitoring System
-- This script runs automatically when PostgreSQL container starts

-- Source systems configuration
CREATE TABLE IF NOT EXISTS source_systems (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    directory_path VARCHAR(500) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SLA definitions
CREATE TABLE IF NOT EXISTS sla_definitions (
    id SERIAL PRIMARY KEY,
    source_system_id VARCHAR(50) REFERENCES source_systems(id) ON DELETE CASCADE,
    expected_arrival_time TIME,
    expected_arrival_window_minutes INT,
    minimum_files_per_day INT,
    weight DECIMAL(3,2) DEFAULT 1.0,
    effective_from DATE NOT NULL,
    effective_to DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_weight CHECK (weight >= 0 AND weight <= 1),
    CONSTRAINT valid_window CHECK (expected_arrival_window_minutes > 0),
    CONSTRAINT valid_min_files CHECK (minimum_files_per_day >= 0)
);

-- SLA violations
CREATE TABLE IF NOT EXISTS sla_violations (
    id SERIAL PRIMARY KEY,
    source_system_id VARCHAR(50) REFERENCES source_systems(id) ON DELETE CASCADE,
    violation_date DATE NOT NULL,
    violation_type VARCHAR(50) NOT NULL,
    expected_value VARCHAR(100),
    actual_value VARCHAR(100),
    severity VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_severity CHECK (severity IN ('low', 'medium', 'high', 'critical'))
);

-- File arrival details
CREATE TABLE IF NOT EXISTS file_arrivals (
    id SERIAL PRIMARY KEY,
    source_system_id VARCHAR(50) REFERENCES source_systems(id) ON DELETE CASCADE,
    filename VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000) NOT NULL,
    arrival_timestamp TIMESTAMP NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    checksum VARCHAR(64),
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_file_size CHECK (file_size_bytes >= 0)
);

-- Configuration audit log
CREATE TABLE IF NOT EXISTS configuration_audit (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100),
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_file_arrivals_timestamp ON file_arrivals(arrival_timestamp);
CREATE INDEX IF NOT EXISTS idx_file_arrivals_source_system ON file_arrivals(source_system_id, arrival_timestamp);
CREATE INDEX IF NOT EXISTS idx_sla_violations_date ON sla_violations(violation_date);
CREATE INDEX IF NOT EXISTS idx_sla_violations_source_system ON sla_violations(source_system_id, violation_date);
CREATE INDEX IF NOT EXISTS idx_config_audit_timestamp ON configuration_audit(timestamp);

-- Insert sample source systems for testing
INSERT INTO source_systems (id, name, directory_path, is_active) VALUES
    ('SYS001', 'Financial System', '/data/sources/financial', true),
    ('SYS002', 'HR System', '/data/sources/hr', true),
    ('SYS003', 'Inventory System', '/data/sources/inventory', true)
ON CONFLICT (id) DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO monitoring_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO monitoring_user;
