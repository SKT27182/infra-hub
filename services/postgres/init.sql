-- =============================================================================
-- Infra Hub - PostgreSQL Initialization Script
-- =============================================================================
-- This script runs on first container startup when the data volume is empty.
-- Use it to create shared databases, schemas, or users for your projects.

-- Create a shared schema for infra management
CREATE SCHEMA IF NOT EXISTS infra;

-- Example: Create application-specific databases
-- Uncomment and modify as needed for your projects

-- CREATE DATABASE project_a;
-- CREATE DATABASE project_b;

-- Example: Create a read-only role for applications
-- CREATE ROLE app_readonly;
-- GRANT CONNECT ON DATABASE infra TO app_readonly;
-- GRANT USAGE ON SCHEMA public TO app_readonly;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_readonly;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'Infra Hub PostgreSQL initialized successfully';
END $$;
