# E-Commerce Product Funnel Analytics

> An end-to-end SQL analysis of an e-commerce product funnel investigating conversion bottlenecks, drop-off rates, and time-to-conversion metrics.

---

## 🎯 Business Problem

A fictional e-commerce platform is experiencing a high volume of new user sign-ups, but lower-than-expected completed purchases. 

This project explores the customer journey to answer:
1. What is the overall conversion rate from signup to purchase?
2. At which specific stage of the product funnel are users dropping off the most?
3. How long does it take for a newly acquired user to make their first purchase?
4. Which geographic markets demonstrate the highest conversion rates?

---

## 📊 Dataset Description

The analysis is based on two core tables (assumed to be a synthetic dataset for educational purposes: `[TODO: Insert dataset source, e.g. Kaggle]`).

*   **`users` table:** 6,000 unique users with signup dates (Jan 1, 2023 - Jun 29, 2023) and country locations.
*   **`events` table:** 19,591 event logs spanning Jan 1, 2023 to Jul 3, 2023. Tracks actions: `signup`, `login`, `view_product`, `add_to_cart`, `purchase`.

*(See `data/README.md` for a complete data dictionary and limitations).*

---

## 🛠 Tools & Technologies

*   **Database:** MySQL (Local / Dockerized)
*   **Data Analysis:** SQL (CTEs, Window Functions, Conditional Aggregation, Joins)
*   **Data Visualization:** Power BI
*   **CI/CD & Linting:** GitHub Actions, `sqlfluff`, `Makefile`

---

## 📁 Project Structure

```text
E-Commerce-Product-Funnel-Analytics/
│
├── data/
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
├── outputs/                # Resulting CSVs from SQL queries
├── dashboard/              # Power BI Dashboard visuals
├── docker-compose.yml      # Local MySQL environment
├── Makefile                # Automation for reproducibility
└── README.md
```

---

## 🔬 Funnel Definition & Methodology

To ensure analytical accuracy, this funnel enforces chronological progression. A user is only counted in Stage N if they completed Stage N-1 on or before the current stage date.

*   **Denominator:** Unique users (`COUNT(DISTINCT user_id)`), *not* total session events.
*   **Funnel Stages:** Signup $\rightarrow$ Login $\rightarrow$ View Product $\rightarrow$ Add to Cart $\rightarrow$ Purchase.
*   *(Note: The dataset does not contain a discrete "checkout" event, so cart abandonment is measured directly from cart to purchase).*

---

## 💡 Key Findings

### 1. Overall Conversion & Drop-off
Out of 6,000 initial signups, **1,298** users successfully completed a purchase, resulting in a **21.6% overall conversion rate**.

*   **Signup:** 6,000 users (100%)
*   **Login:** 5,396 users (89.9%)
*   **View Product:** 4,320 users (72.0%)
*   **Add to Cart:** 2,577 users (42.9%)
*   **Purchase:** 1,298 users (21.6%)

**Critical Bottleneck:** The largest absolute percentage drop-off occurs between **Add to Cart and Purchase**, where roughly **49.7%** of users who add an item to their cart fail to complete the transaction.

### 2. Time to Convert
The majority of converting users purchase relatively quickly:
*   **Within 1 Week:** 85.9% of purchasers convert between 2 and 7 days after signup.
*   **Next Day:** 11.2% convert the day after signing up.
*   **Same Day:** Only 2.8% convert on the exact same day they sign up.

### 3. Geographic Performance
*   **Top Market:** Germany leads with the highest conversion rate at **22.6%** (227 purchasers out of 1003 signups).
*   **Lagging Market:** The UK lags slightly behind with a **20.5%** conversion rate.

---

## 📈 Recommendations

1.  **Target Cart Abandonment:** Since nearly 50% of users drop off after adding to their cart, implementing an automated "abandoned cart" email drip campaign or offering a limited-time 10% discount at the cart stage could immediately lift the final conversion rate.
2.  **Optimize the First Week:** Because 85% of purchases happen within the first week of signup, marketing and product onboarding should be heavily front-loaded in the first 7 days.
3.  **Investigate UK Friction:** Product teams should investigate localization, shipping costs, or payment methods in the UK to understand why it converts 200 basis points lower than Germany.

---

## 📊 Dashboard Rebuild Instructions

`[TODO: Add the published Power BI link here]`
`[TODO: Place your actual dashboard.pbix file in the /dashboard folder]`

The dashboard visuals (`dashboard/dashboard.png`) can be perfectly rebuilt by importing the `outputs/*.csv` tables into Power BI.
*   **Funnel Chart:** Uses `outputs/02_funnel_metrics.csv` (`stage` as Category, `users` as Values).
*   **Bar Chart (Time to Convert):** Uses `outputs/03_time_to_convert.csv` (`time_bucket` on X, `percentage` on Y).

---

## ⚙️ How to Reproduce

You can reproduce this exact analysis locally with a single command using Docker.

1. Clone this repository.
2. Run the Makefile to spin up MySQL, load the data, and execute all queries:
   ```bash
   make up
   make run-queries
   ```
3. The resulting metrics will be saved exactly as seen in the `outputs/` folder.
4. Run `make down` to spin down the database.

---

## 🌱 What I Learned / Next Steps

*   **Chronological Funnels:** I learned the importance of enforcing chronological sequence in funnel analytics rather than just relying on aggregate cross-sectional counts, which can skew the reality of the user journey.
*   **Data Portability:** Structuring SQL into discrete steps and exporting to CSVs taught me how to properly hand off clean analytical data to a BI tool like Power BI without requiring heavy DAX logic.
*   **Next Steps:** If timestamp data were available, I would analyze session-level drop-offs (e.g., minutes from cart to purchase) rather than just day-level metrics.

---

**Author:** `[TODO: YOUR NAME]` | `[TODO: LinkedIn Link]` | `[TODO: Portfolio Link]`
