-- Distribution among observed purchasers only. This is not a conversion
-- probability because newer signup cohorts have shorter observation windows.
USE ecommerce_analytics;

WITH signup_stage AS (
    SELECT user_id, MIN(event_date) AS signup_date
    FROM events
    WHERE event_type = 'signup'
    GROUP BY user_id
),

first_qualified_purchase AS (
    SELECT
        s.user_id,
        s.signup_date,
        MIN(e.event_date) AS purchase_date
    FROM signup_stage AS s
    JOIN events AS e
        ON
            e.user_id = s.user_id
            AND e.event_type = 'purchase'
            AND e.event_date >= s.signup_date
    GROUP BY s.user_id, s.signup_date
),

observed_purchasers AS (
    SELECT
        user_id,
        DATEDIFF(purchase_date, signup_date) AS days_elapsed
    FROM first_qualified_purchase
),

bucket_list AS (
    SELECT 0 AS sort_order, '0_Same_Day' AS time_bucket
    UNION ALL
    SELECT 1 AS sort_order, '1_Next_Day' AS time_bucket
    UNION ALL
    SELECT 2 AS sort_order, '2_Within_Week' AS time_bucket
    UNION ALL
    SELECT 3 AS sort_order, '3_More_Than_Week' AS time_bucket
),

bucket_counts AS (
    SELECT
        CASE
            WHEN days_elapsed = 0 THEN '0_Same_Day'
            WHEN days_elapsed = 1 THEN '1_Next_Day'
            WHEN days_elapsed BETWEEN 2 AND 7 THEN '2_Within_Week'
            ELSE '3_More_Than_Week'
        END AS time_bucket,
        COUNT(*) AS observed_purchasers
    FROM observed_purchasers
    GROUP BY time_bucket
),

total_observed AS (
    SELECT COUNT(*) AS total_purchasers
    FROM observed_purchasers
)

SELECT
    b.time_bucket,
    COALESCE(c.observed_purchasers, 0) AS observed_purchasers,
    ROUND(
        COALESCE(c.observed_purchasers, 0) * 100.0
        / NULLIF(t.total_purchasers, 0),
        2
    ) AS percentage_of_observed_purchasers
FROM bucket_list AS b
LEFT JOIN bucket_counts AS c ON c.time_bucket = b.time_bucket
CROSS JOIN total_observed AS t
ORDER BY b.sort_order;
