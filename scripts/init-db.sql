-- Initialize PostgreSQL database for Council DA Scraper
-- This script runs automatically when the container starts

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create schema
CREATE SCHEMA IF NOT EXISTS council_da;

-- Set search path
SET search_path TO council_da, public;

-- Create indexes for common queries (tables created by SQLAlchemy)
-- These are additional performance indexes

-- Note: Main tables are created by SQLAlchemy migrations
-- This file sets up extensions and can add additional custom indexes or functions

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Function for full-text search
CREATE OR REPLACE FUNCTION search_applications(
    search_query TEXT,
    council_filter TEXT DEFAULT NULL,
    status_filter TEXT DEFAULT NULL,
    category_filter TEXT DEFAULT NULL,
    limit_count INTEGER DEFAULT 50,
    offset_count INTEGER DEFAULT 0
)
RETURNS TABLE (
    id UUID,
    da_number TEXT,
    address TEXT,
    suburb TEXT,
    description TEXT,
    status TEXT,
    category TEXT,
    lodged_date TIMESTAMP,
    rank REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        a.id,
        a.da_number,
        a.address,
        a.suburb,
        a.description,
        a.status,
        a.category,
        a.lodged_date,
        ts_rank(
            setweight(to_tsvector('english', COALESCE(a.address, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(a.description, '')), 'B'),
            plainto_tsquery('english', search_query)
        ) AS rank
    FROM council_da.applications a
    WHERE (
        to_tsvector('english', COALESCE(a.address, '') || ' ' || COALESCE(a.description, ''))
        @@ plainto_tsquery('english', search_query)
    )
    AND (council_filter IS NULL OR a.council_code = council_filter)
    AND (status_filter IS NULL OR a.status = status_filter)
    AND (category_filter IS NULL OR a.category = category_filter)
    ORDER BY rank DESC, a.lodged_date DESC NULLS LAST
    LIMIT limit_count
    OFFSET offset_count;
END;
$$ LANGUAGE plpgsql;

-- Function to find applications within radius
CREATE OR REPLACE FUNCTION find_applications_near(
    lat DOUBLE PRECISION,
    lng DOUBLE PRECISION,
    radius_meters DOUBLE PRECISION DEFAULT 5000,
    limit_count INTEGER DEFAULT 50
)
RETURNS TABLE (
    id UUID,
    da_number TEXT,
    address TEXT,
    suburb TEXT,
    description TEXT,
    status TEXT,
    category TEXT,
    distance_meters DOUBLE PRECISION
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        a.id,
        a.da_number,
        a.address,
        a.suburb,
        a.description,
        a.status,
        a.category,
        ST_Distance(
            a.coordinates::geography,
            ST_SetSRID(ST_MakePoint(lng, lat), 4326)::geography
        ) AS distance_meters
    FROM council_da.applications a
    WHERE a.coordinates IS NOT NULL
    AND ST_DWithin(
        a.coordinates::geography,
        ST_SetSRID(ST_MakePoint(lng, lat), 4326)::geography,
        radius_meters
    )
    ORDER BY distance_meters
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Materialized view for statistics (refresh periodically)
CREATE MATERIALIZED VIEW IF NOT EXISTS council_da.application_stats AS
SELECT
    council_code,
    COUNT(*) as total_applications,
    COUNT(*) FILTER (WHERE lodged_date >= CURRENT_DATE - INTERVAL '30 days') as last_30_days,
    COUNT(*) FILTER (WHERE lodged_date >= CURRENT_DATE - INTERVAL '7 days') as last_7_days,
    COUNT(DISTINCT category) as unique_categories,
    AVG(COALESCE(estimated_cost, 0)) FILTER (WHERE estimated_cost > 0) as avg_cost,
    MAX(scraped_at) as last_scraped
FROM council_da.applications
GROUP BY council_code;

-- Index on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_stats_council ON council_da.application_stats (council_code);

-- Grant permissions
GRANT USAGE ON SCHEMA council_da TO PUBLIC;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA council_da TO PUBLIC;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA council_da TO PUBLIC;
