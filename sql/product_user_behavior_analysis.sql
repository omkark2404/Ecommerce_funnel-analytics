-- Create and use database
CREATE DATABASE IF NOT EXISTS ecommerce_analytics;
USE ecommerce_analytics;

-- --------------------------------------------------------
-- 1. SCHEMA DEFINITION & OPTIMIZATION
-- --------------------------------------------------------

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

-- --------------------------------------------------------
-- 2. DATA QUALITY CHECKS
-- --------------------------------------------------------
-- Quick check of table row counts
SELECT 'Events Count' AS metric, COUNT(*) AS total FROM events
UNION ALL
SELECT 'Users Count' AS metric, COUNT(*) AS total FROM users;

-- --------------------------------------------------------
-- 3. FUNNEL ANALYSIS (CORRECTED LOGIC)
-- --------------------------------------------------------

-- Query 1: Total users at each stage
SELECT 
    event_type,
    COUNT(DISTINCT user_id) AS unique_users
FROM events
GROUP BY event_type
ORDER BY unique_users DESC;

-- Query 2: Overall Conversion Rate (Signup to Purchase)
WITH user_stages AS (
    SELECT 
        user_id,
        MAX(CASE WHEN event_type = 'signup' THEN 1 ELSE 0 END) AS signed_up,
        MAX(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS purchased
    FROM events
    GROUP BY user_id
)
SELECT 
    SUM(signed_up) AS total_signups,
    SUM(purchased) AS total_purchases,
    ROUND((SUM(purchased) * 100.0) / NULLIF(SUM(signed_up), 0), 2) AS overall_conversion_rate
FROM user_stages;

-- Query 3: Stage-to-Stage Drop-off & Conversion (Linear Funnel using Window Functions)
WITH funnel_stages AS (
    -- Define the expected sequence of stages
    SELECT 'signup' AS event_type, 1 AS stage_order
    UNION ALL SELECT 'login', 2
    UNION ALL SELECT 'view_product', 3
    UNION ALL SELECT 'add_to_cart', 4
    UNION ALL SELECT 'purchase', 5
),
stage_counts AS (
    -- Count distinct users per stage
    SELECT 
        fs.stage_order,
        fs.event_type,
        COUNT(DISTINCT e.user_id) AS users
    FROM funnel_stages fs
    LEFT JOIN events e ON fs.event_type = e.event_type
    GROUP BY fs.stage_order, fs.event_type
)
SELECT 
    event_type AS current_stage,
    users AS current_users,
    LAG(users) OVER (ORDER BY stage_order) AS previous_users,
    LAG(users) OVER (ORDER BY stage_order) - users AS drop_off_count,
    ROUND((users * 100.0) / NULLIF(LAG(users) OVER (ORDER BY stage_order), 0), 2) AS stage_conversion_rate_pct
FROM stage_counts
ORDER BY stage_order;


-- Query 4: True Funnel Progression Check (Chronological limitation noted)
-- Note: Since event_date is DATE and not TIMESTAMP, exact time-of-day progression 
-- cannot be strictly enforced if multiple events occur on the same day. 
-- A robust funnel usually requires event_date to be cast/stored as TIMESTAMP.

-- --------------------------------------------------------
-- 4. BUSINESS INSIGHTS (Using the `users` table)
-- --------------------------------------------------------

-- Query 5: Conversion Rate by Country (Joining Users & Events)
WITH country_purchases AS (
    SELECT 
        u.country,
        COUNT(DISTINCT u.user_id) AS total_users,
        COUNT(DISTINCT CASE WHEN e.event_type = 'purchase' THEN e.user_id END) AS purchasing_users
    FROM users u
    LEFT JOIN events e ON u.user_id = e.user_id
    GROUP BY u.country
)
SELECT 
    country,
    total_users,
    purchasing_users,
    ROUND((purchasing_users * 100.0) / NULLIF(total_users, 0), 2) AS conversion_rate_pct
FROM country_purchases
ORDER BY conversion_rate_pct DESC, total_users DESC;

-- Query 6: Time to Conversion (Average days from Signup to Purchase)
WITH signup_dates AS (
    SELECT user_id, MIN(event_date) AS signup_date 
    FROM events WHERE event_type = 'signup' GROUP BY user_id
),
purchase_dates AS (
    SELECT user_id, MIN(event_date) AS purchase_date 
    FROM events WHERE event_type = 'purchase' GROUP BY user_id
)
SELECT 
    ROUND(AVG(DATEDIFF(p.purchase_date, s.signup_date)), 2) AS avg_days_to_purchase
FROM signup_dates s
JOIN purchase_dates p ON s.user_id = p.user_id;