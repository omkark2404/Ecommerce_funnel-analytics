# Dashboard Rebuild Instructions

The dashboard visual (`dashboard/dashboard.png`) was built using Power BI, but the `.pbix` file is not currently tracked in this repository. `[TODO: Place your actual dashboard.pbix file in the /dashboard folder]`

`[TODO: Add the published Power BI web link here]`

## Rebuilding from Outputs

If you want to recreate the dashboard visuals, you do NOT need to write complex DAX or connect directly to a database. You can simply import the clean, aggregated tables from the `outputs/` folder:

1.  **Funnel Visual:**
    *   **Source:** `outputs/02_funnel_metrics.csv`
    *   **Fields:** Category = `stage`, Values = `users`.
2.  **Time-to-Convert Bar Chart:**
    *   **Source:** `outputs/03_time_to_convert.csv`
    *   **Fields:** X-Axis = `time_bucket`, Y-Axis = `percentage`.
3.  **KPI Cards:**
    *   **Total Users:** `SUM(users)` from `02_funnel_metrics.csv` where `stage = '1_signup'`.
    *   **Total Conversions:** `SUM(users)` where `stage = '5_purchase'`.
    *   **Conversion Rate:** `Total Conversions / Total Users`.
4.  **Country Segmentation Table:**
    *   **Source:** `outputs/04_country_segmentation.csv`
    *   **Fields:** `country`, `total_users`, `total_purchases`, `conversion_rate_pct`.
