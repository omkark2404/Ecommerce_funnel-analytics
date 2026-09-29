# E-Commerce Product Funnel Analytics

> End-to-end SQL analysis of an e-commerce product funnel identifying conversion bottlenecks (Signup to Purchase). Includes reproducible SQL scripts, stage-to-stage drop-off rates, time-to-conversion metrics, and geographic segmentation.

---

## 🎯 Business Problem & Objective

A fictional e-commerce platform is experiencing a high volume of new user sign-ups, but it is unclear where users are dropping off before completing a purchase. 

**Objective:** Map the exact user journey to pinpoint the largest drop-off stages in the product funnel, analyze how quickly users convert, and identify geographical differences in conversion rates to guide product optimization.

---

## 📊 Dataset Description

The analysis is based on two core tables representing a completely clean, uniform dataset. Given the perfect data distributions, **this dataset is assumed to be synthetically generated** for educational/portfolio purposes.
*   **Source:** `[TODO: Insert dataset source, e.g. Kaggle, Maven Analytics, etc.]`
*   **`product_users_clean.csv`:** 6,000 unique users. Contains `signup_date` (2023-01-01 to 2023-06-29) and `country`.
*   **`product_events_clean.csv`:** 19,591 event logs for the 6,000 users spanning 2023-01-01 to 2023-07-03. Tracks strictly 5 actions: `signup`, `login`, `view_product`, `add_to_cart`, `purchase`.

*(See `data/README.md` for the complete data dictionary).*

---

## 🛠 Tools & Technologies

*   **Database:** MySQL (Local / Dockerized)
*   **Data Analysis:** SQL (CTEs, Window Functions, Conditional Aggregation, Joins)
*   **Data Visualization:** Python (Matplotlib/Seaborn) & Power BI
*   **CI/CD:** GitHub Actions (MySQL Service Container), `sqlfluff` for Linting

---

## 📁 Project Structure

```text
E-Commerce-Product-Funnel-Analytics/
│
├── data/
│   ├── README.md
│   ├── product_users_clean.csv
│   └── product_events_clean.csv
│
├── sql/
│   ├── 00_schema.sql
│   ├── 01_load_data.sql
│   ├── 02_funnel_metrics.sql
│   ├── 03_time_to_convert.sql
│   └── 04_country_segmentation.sql
│
├── outputs/
│   ├── 02_funnel_metrics.csv
│   ├── 03_time_to_convert.csv
│   ├── 04_country_segmentation.csv
│   └── figures/                  # Generated funnel charts
│
├── dashboard/                    
│   ├── README.md                 # Instructions to rebuild the dashboard
│   └── dashboard.png             # Power BI Dashboard visual preview
│
├── docker-compose.yml            # Local MySQL environment
├── Makefile                      # Automation for reproducibility
└── README.md
```

---

## 🔬 Methodology & Metric Definitions

To ensure analytical accuracy, this funnel enforces chronological progression. A user is only counted in Stage N if they completed Stage N-1 on or before the current stage date.

*   **Metric Granularity:** Unique users (`COUNT(DISTINCT user_id)` or `COUNT(user_id)` grouped by user), *not* total session events.
*   **Stage-to-Stage Conversion Rate Formula:** `(Users in Stage N) / (Users in Stage N-1)`
*   **Overall Conversion Rate Formula:** `(Users in Purchase Stage) / (Users in Signup Stage)`
*   *(Note: The dataset does not contain a discrete "checkout" event, so drop-off is measured directly from "add_to_cart" to "purchase").*

---

## 💡 Key Findings

### 1. Overall Conversion & Drop-off
Out of 6,000 initial signups, **1,298** users successfully completed a purchase, resulting in a **21.6% overall conversion rate**.

![Funnel Chart](outputs/figures/funnel_chart.png)

*   **Signup:** 6,000 users (100%)
*   **Login:** 5,396 users (89.9%)
*   **View Product:** 4,320 users (72.0%)
*   **Add to Cart:** 2,577 users (42.9%)
*   **Purchase:** 1,298 users (21.6%)

**Critical Bottleneck:** The largest percentage drop-off relative to the previous stage occurs between **Add to Cart and Purchase**. Out of 2,577 users who added an item to their cart, only 1,298 purchased, representing a massive **49.6% drop-off** at the final hurdle.

![Drop-off Chart](outputs/figures/dropoff_chart.png)

### 2. Time to Convert
The majority of converting users purchase relatively quickly:
*   **Within 1 Week:** 86.0% (1,116 users) of purchasers convert between 2 and 7 days after signup.
*   **Next Day:** 11.2% (145 users) convert the day after signing up.
*   **Same Day:** Only 2.9% (37 users) convert on the exact same day they sign up.

![Time to Convert](outputs/figures/time_to_convert.png)

### 3. Geographic Performance
*   **Top Market:** Germany leads with the highest conversion rate at **22.63%** (227 purchasers / 1003 signups).
*   **Lagging Market:** The UK lags slightly behind with a **20.52%** conversion rate (198 purchasers / 965 signups).
*   *(Note: Due to the nearly identical segment sizes (950-1050 users per country) and tight conversion spread (20.5% - 22.6%), these differences are largely descriptive and may not represent highly significant shifts in user behavior without further statistical testing).*

---

## 📈 Recommendations

1.  **Target Cart Abandonment:** Because nearly 50% of users drop off after adding an item to their cart, implementing an automated "abandoned cart" email drip campaign or surfacing a limited-time 10% discount during the cart review stage could yield an immediate lift in overall conversions.
2.  **Optimize the First Week Onboarding:** Because 86% of purchases happen between Day 2 and Day 7 post-signup, marketing (like retargeting ads) and product onboarding should be heavily front-loaded during this critical 7-day window.
3.  **Investigate UK Friction:** Product teams should audit the UK user journey (e.g., localization, shipping costs, payment methods) to understand why it converts 200 basis points lower than Germany.

*(Assumption: These recommendations assume the drop-off is driven by user friction rather than platform bugs or inventory stock-outs).*

---

## ⚙️ How to Reproduce

You can reproduce this exact analysis locally with a single command using Docker and `make`.

1. Clone this repository.
2. Spin up the MySQL container and load the raw data:
   ```bash
   make up
   ```
3. Execute the SQL queries (which will automatically write the results to `outputs/*.csv`):
   ```bash
   make run-queries
   ```
4. Tear down the database:
   ```bash
   make down
   ```

---

## ⚠️ Limitations & Assumptions

1. **Date Granularity:** The `event_date` field is recorded at the `DATE` level, not `TIMESTAMP`. Because users frequently trigger multiple events on the exact same day, strict chronological ordering *within* a single day cannot be perfectly enforced. The SQL logic assumes events occurring on the same day follow the logical funnel progression.
2. **Missing Raw Data:** The provided dataset was already in a `_clean` state. The raw data and the data cleaning steps (e.g., Python/Pandas transformation) are not documented or included.

---

## 🌱 What I Learned / Next Steps

*   **Chronological Funnels in SQL:** I learned how to use Conditional Aggregation (`MIN(CASE WHEN...)`) to enforce chronological sequence in funnel analytics rather than relying on aggregate cross-sectional counts, which can skew the reality of the user journey.
*   **Data Portability for BI:** Splitting SQL into discrete execution steps and exporting directly to CSVs taught me how to cleanly hand off analytical data to a BI tool like Power BI without requiring heavy DAX transformations.
*   **Next Steps:** If timestamp data were available, my next step would be analyzing session-level cart abandonment (e.g., minutes elapsed from cart to purchase) to better target retargeting campaigns.

---

**Author:** `[TODO: YOUR NAME]` 
**Contact:** `[TODO: LinkedIn Link]` | `[TODO: Portfolio Link]`
