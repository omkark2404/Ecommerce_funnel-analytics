# Data documentation

This directory contains the cleaned CSV inputs used by the analysis. The original raw files and cleaning script are not included.

## product_users_clean.csv

- 6,000 unique accounts.
- Signup dates range from 2023-01-01 through 2023-06-29.
- Fields: user_id, signup_date, country.

## product_events_clean.csv

- 19,591 user-level event rows.
- Event dates range from 2023-01-01 through 2023-07-03.
- Fields: user_id, event_type, event_date.
- Event types: signup, login, view_product, add_to_cart, purchase.

The files contain no session, order, product, quantity, price, or timestamp fields. The event date is recorded at day granularity. Where multiple funnel stages share a date, the analysis treats them as occurring in the intended stage order; the data cannot verify that order.

The original data publisher and generator were not recorded. The clean distributions suggest a synthetic demonstration dataset, but this repository does not claim a specific source or authoring process. Treat all results as illustrative.

The checked-in CSV files are maintained with LF line endings. Dataset checks and artifact generation are available in scripts/build_artifacts.py.
