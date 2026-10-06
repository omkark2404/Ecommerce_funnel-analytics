# Dashboard preview

dashboard.png is a static PNG generated from the checked-in analysis results by scripts/build_artifacts.py. It summarizes the funnel, observed purchase timing, country-level descriptive rates, and the mature seven-day conversion measure.

There is no Power BI project file or published dashboard link in this repository. The PNG is a preview, not an interactive dashboard.

Regenerate all result CSVs and visuals from the bundled source data with:

    python scripts/build_artifacts.py

Check that the committed artifacts match the reproducible build with:

    python scripts/build_artifacts.py --check
