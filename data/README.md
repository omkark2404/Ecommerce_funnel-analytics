# Data Documentation

This folder contains the cleaned datasets used for the E-Commerce Product Funnel Analytics project.

## Datasets

### 1. `product_users_clean.csv`
Contains demographic and acquisition information for platform users.

*   **Row Count:** 6,000
*   **Date Range (`signup_date`):** 2023-01-01 to 2023-06-29
*   **Null Values:** 0
*   **Dictionary:**
    *   `user_id` (Integer): Unique identifier for the user.
    *   `signup_date` (Date): The date the user created their account (YYYY-MM-DD format).
    *   `country` (String): The user's registered country.

### 2. `product_events_clean.csv`
Contains event logs tracking the user journey through the product funnel.

*   **Row Count:** 19,591
*   **Date Range (`event_date`):** 2023-01-01 to 2023-07-03
*   **Null Values:** 0
*   **Unique Users Logged:** 6,000
*   **Dictionary:**
    *   `user_id` (Integer): Identifier linking to the `users` table.
    *   `event_type` (String): The action performed. Values: `signup`, `login`, `view_product`, `add_to_cart`, `purchase`. *(Note: There is no distinct 'checkout' event in this dataset).*
    *   `event_date` (Date): The date the action occurred.

## Limitations & Assumptions
1. **Source:** `[TODO: Insert dataset source, e.g., Kaggle, company sample, etc.]`. Due to the perfectly clean distributions and lack of nulls, this dataset is assumed to be synthetic/generated for educational purposes.
2. **Date Granularity:** The `event_date` field is recorded at the `DATE` level, not `TIMESTAMP`. Because users frequently trigger multiple events on the exact same day, strict chronological ordering *within* a single day cannot be perfectly enforced. The analysis assumes events occurring on the same day follow the logical funnel progression.
3. **Data Cleaning:** The raw, uncleaned data and the exact cleaning script (e.g., Python/Pandas steps) are not included in this repository. These files represent the final, clean state ready for SQL consumption.
