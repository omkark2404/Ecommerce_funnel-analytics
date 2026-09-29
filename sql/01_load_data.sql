-- ======================================================================
-- 01_load_data.sql
-- Business Purpose: Load the raw CSV data into the MySQL tables.
-- Note: Update the file path to match your local environment's secure-file-priv directory.
-- ======================================================================

USE ecommerce_analytics;

-- Load Users Data
LOAD DATA INFILE '/var/lib/mysql-files/product_users_clean.csv'
INTO TABLE users
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(user_id, signup_date, country);

-- Load Events Data
LOAD DATA INFILE '/var/lib/mysql-files/product_events_clean.csv'
INTO TABLE events
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(user_id, event_type, event_date);
