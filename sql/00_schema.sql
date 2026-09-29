-- ======================================================================
-- 00_schema.sql
-- Business Purpose: Create the database and define the tables with proper 
-- data types and relationships to ensure data integrity and performance.
-- ======================================================================

CREATE DATABASE IF NOT EXISTS ecommerce_analytics;
USE ecommerce_analytics;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    user_id INT PRIMARY KEY,
    signup_date DATE,
    country VARCHAR(100)
);

-- Create events table
CREATE TABLE IF NOT EXISTS events (
    user_id INT,
    event_type VARCHAR(50),
    event_date DATE,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Add indexes for better query performance on large datasets
CREATE INDEX idx_user_id ON events(user_id);
CREATE INDEX idx_event_type ON events(event_type);
