-- ======================================================================
-- 03_time_to_convert.sql
-- Business Purpose: Calculate the distribution of days it takes for a user 
-- to convert from their initial signup to their first purchase.
-- ======================================================================

USE ecommerce_analytics;

WITH user_dates AS (
    SELECT 
        user_id,
        MIN(CASE WHEN event_type = 'signup' THEN event_date END) AS signup_date,
        MIN(CASE WHEN event_type = 'purchase' THEN event_date END) AS purchase_date
    FROM events
    GROUP BY user_id
),
days_to_convert AS (
    SELECT 
        user_id,
        DATEDIFF(purchase_date, signup_date) AS days_elapsed
    FROM user_dates
    WHERE purchase_date IS NOT NULL AND purchase_date >= signup_date
)
SELECT 
    CASE 
        WHEN days_elapsed = 0 THEN '0_Same_Day'
        WHEN days_elapsed = 1 THEN '1_Next_Day'
        WHEN days_elapsed BETWEEN 2 AND 7 THEN '2_Within_Week'
        ELSE '3_More_Than_Week'
    END AS time_bucket,
    COUNT(user_id) AS total_users,
    ROUND(COUNT(user_id) * 100.0 / (SELECT COUNT(*) FROM days_to_convert), 2) AS percentage
FROM days_to_convert
GROUP BY time_bucket
ORDER BY time_bucket;
