-- ======================================================================
-- 02_funnel_metrics.sql
-- Business Purpose: Calculate the exact drop-off between funnel stages.
-- Logic: To ensure chronological progression, we identify the FIRST time a user 
-- performed each action, and ensure subsequent actions happened on or after that date.
-- ======================================================================

USE ecommerce_analytics;

WITH user_stage_dates AS (
    SELECT 
        user_id,
        MIN(CASE WHEN event_type = 'signup' THEN event_date END) AS signup_date,
        MIN(CASE WHEN event_type = 'login' THEN event_date END) AS login_date,
        MIN(CASE WHEN event_type = 'view_product' THEN event_date END) AS view_date,
        MIN(CASE WHEN event_type = 'add_to_cart' THEN event_date END) AS cart_date,
        MIN(CASE WHEN event_type = 'purchase' THEN event_date END) AS purchase_date
    FROM events
    GROUP BY user_id
),
funnel_counts AS (
    SELECT 
        -- Stage 1: Signup
        COUNT(signup_date) AS signups,
        
        -- Stage 2: Login (must occur on or after signup)
        COUNT(CASE WHEN login_date >= signup_date THEN user_id END) AS logins,
        
        -- Stage 3: View Product (must occur on or after login)
        COUNT(CASE WHEN view_date >= login_date THEN user_id END) AS product_views,
        
        -- Stage 4: Add to Cart (must occur on or after product view)
        COUNT(CASE WHEN cart_date >= view_date THEN user_id END) AS cart_adds,
        
        -- Stage 5: Purchase (must occur on or after add to cart)
        COUNT(CASE WHEN purchase_date >= cart_date THEN user_id END) AS purchases
    FROM user_stage_dates
)
SELECT 
    '1_signup' AS stage, signups AS users, NULL AS previous_stage_users, 100.00 AS conversion_from_start
FROM funnel_counts
UNION ALL
SELECT 
    '2_login', logins, signups, ROUND((logins * 100.0) / NULLIF(signups, 0), 2)
FROM funnel_counts
UNION ALL
SELECT 
    '3_view_product', product_views, logins, ROUND((product_views * 100.0) / NULLIF(logins, 0), 2)
FROM funnel_counts
UNION ALL
SELECT 
    '4_add_to_cart', cart_adds, product_views, ROUND((cart_adds * 100.0) / NULLIF(product_views, 0), 2)
FROM funnel_counts
UNION ALL
SELECT 
    '5_purchase', purchases, cart_adds, ROUND((purchases * 100.0) / NULLIF(cart_adds, 0), 2)
FROM funnel_counts;
