# EV Managed Charging Simulation under PG&E's Hourly Flexible Pricing (HFP)

Simulates residential EV charging load profiles across PG&E service territory and quantifies the impact of managed charging adoption under hourly flexible pricing (HFP).

## How It Works

1. **Geospatial matching** — 59 [PG&E feeders](https://grip.pge.com) are spatially joined to [California zip codes](https://gis.data.ca.gov/datasets/ca-zip-code-boundaries/about). Top EV-adoption zip codes (from [CA EV sales data](https://www.energy.ca.gov/files/zev-and-infrastructure-stats-data)) without a direct feeder match are assigned the nearest feeder.

2. **Pricing data** — Hourly EV2A rate prices for 2025 are pulled from [PG&E's GridX API](https://api-calculate-docs.gridx.com/calculate-apis-gridx-docs/api-introduction-overview) for each feeder under the [Hourly Flexible Pricing](https://www.pge.com/en/account/rate-plans/hourly-flex-pricing.html) program.

3. **Profile generation** — 2,500 annual vehicle charging profiles are generated using real-world [plugin/charging distributions](https://zenodo.org/records/17353155). Each profile is a sequence of sessions with plugin start/end hours and a binary charging array.

4. **Optimization** — For every feeder, each profile's charging hours are optimized to the cheapest-priced hours within each plugin window (total charging energy unchanged).

5. **Dashboard** — Users select a zip code and managed charging adoption rate. The app samples profiles with replacement, applies optimization to the adopted fraction, and displays aggregated load results.

## Quick Start

```bash
pip install streamlit pandas numpy plotly
cd pge_hfp_ev_charging_load
streamlit run app.py
```

## Repository Structure

```
modo/
├── app.py                          # Streamlit dashboard
├── exploratory_notebook.ipynb      # All exploratory and generation code
├── data/
│   ├── final_data.csv              # Zip-feeder-EV count mapping
│   ├── pge_hfp_pricing_2025.csv    # Hourly pricing per feeder (2025)
│   ├── ev_charging_session_distribution.csv
│   ├── ca_ev_sales_zip_level.csv
│   └── ev_charging_profile_database/
│       └── sample_{1..2500}.json   # Pre-computed vehicle profiles
```

## Dashboard Outputs

- **EV Charging Load Profile** — Annual hourly load (baseline vs managed charging)
- **Change in Annual Peak Demand** — Hourly peak demand shift (% change)
- **Annual Average Daily Load Profile** — Smoothed typical daily shape
