-- ======================================================================
-- 04_country_segmentation.sql
-- Business Purpose: Identify which geographical markets have the highest 
-- overall conversion rate (Signup -> Purchase) to guide marketing spend.
-- ======================================================================

USE ecommerce_analytics;

WITH user_conversion AS (
    SELECT 
        u.user_id,
        u.country,
        MAX(CASE WHEN e.event_type = 'purchase' THEN 1 ELSE 0 END) AS has_purchased
    FROM users u
    LEFT JOIN events e ON u.user_id = e.user_id
    GROUP BY u.user_id, u.country
)
SELECT 
    country,
    COUNT(user_id) AS total_users,
    SUM(has_purchased) AS total_purchases,
    ROUND(SUM(has_purchased) * 100.0 / COUNT(user_id), 2) AS conversion_rate_pct
FROM user_conversion
GROUP BY country
ORDER BY conversion_rate_pct DESC;
