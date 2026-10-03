# E-Commerce Sales Analysis — Olist (Brazil, 2016–2018)

An end-to-end data analyst project on ~100k real orders from Olist, Brazil's
largest marketplace: **SQL → Python → Power BI**.

## Business questions

1. What are the headline KPIs — revenue, orders, average order value?
2. Is revenue growing month over month?
3. Which product categories drive revenue — and which ones drag?
4. How reliable is delivery, and does lateness hurt customer satisfaction?
5. How do customers pay, and how do installments scale with basket size?
6. Where does freight (shipping) eat the margin?

## Dataset

Olist public e-commerce data (CC BY-SA 4.0):
https://github.com/olist/work-at-olist-data

| Table | Rows | Contents |
|---|---|---|
| orders | 99,441 | order lifecycle, timestamps, status |
| order_items | 112,650 | price & freight per item |
| payments | 103,886 | payment type, installments, value |
| reviews | 99,224 | 1–5 star scores + comments |
| customers | 99,441 | anonymized customers, city/state |
| products | 32,951 | category, dimensions, weight |
| sellers | 3,095 | seller city/state |

Run `python python/download_data.py` to fetch the raw CSVs into `data/raw/`.

## Tech stack

- **SQL (PostgreSQL)** — schema, data cleaning, business analysis (`sql/`)
- **Python (pandas, NumPy, matplotlib)** — EDA notebook (`python/analysis_notebook.ipynb`)
- **Power BI** — interactive dashboard from the cleaned fact table (`powerbi/`)

## Project structure

```
├── sql/
│   ├── 01_schema.sql        # table definitions (PostgreSQL)
│   ├── 02_data_cleaning.sql # documented data-quality fixes
│   └── 03_analysis.sql      # 10 business-question queries
├── python/
│   ├── download_data.py     # fetches raw CSVs
│   ├── build_notebook.py    # regenerates the notebook + fact table
│   ├── build_dashboard.py   # regenerates the HTML dashboard
│   └── analysis_notebook.ipynb
├── powerbi/
│   ├── fact_orders_clean.csv # 112,650 rows, 18 cols — generated locally via
│   │                         # build_notebook.py (not committed: GitHub file-size limits)
│   └── POWERBI_GUIDE.md      # Power BI Desktop build plan + DAX measures
├── dashboard/
│   ├── olist_dashboard.html  # finished interactive dashboard (open in browser)
│   └── preview.png
└── README.md
```

## Methodology

1. **Profile** every table: row counts, nulls, duplicates, date ranges, orphans.
2. **Clean** with documented rules (never mutate raw data — `*_clean` tables):
   - 166 orders had `order_delivered_carrier_date` *before* the purchase
     timestamp (logging error) → carrier date nulled, order kept.
   - 814 duplicate `review_id`s → kept the latest review per id.
   - 9 payments with `payment_value <= 0` → excluded.
   - 610 products missing category → labeled `unknown`; 2 missing
     dimensions left NULL (missing ≠ zero).
3. **Analyze** in SQL (10 queries) and Python (EDA notebook).
4. **Visualize** in Power BI from the cleaned fact table.

## Key findings

- **R$13.2M revenue** across 96,478 delivered orders (97% of all orders);
  **AOV R$137**, freight cost R$2.2M. 93k unique customers, 2,970 sellers.
- **Top 3 categories** (health & beauty R$1.23M, watches & gifts R$1.17M,
  bed/bath/table R$1.02M) drive **~26% of revenue**; tail categories
  (flowers, CDs/DVDs, kids' fashion) are negligible.
- **8.1% of orders arrive late** (7,827 orders). Late orders score
  **2.6/5 vs 4.3/5** for on-time — delivery reliability is the single
  biggest lever on satisfaction.
- **Lateness concentrates in the North/Northeast**: MA 19.7%, CE 15.3%,
  BA 14.0% late (vs ~8% average), with 21+ day average transits.
- **Credit card = 74% of payments**; installments rise from **2.0×** on
  baskets under R$100 to **5.3×** on baskets over R$300.
- **Freight burden is heaviest on bulky goods**: electronics ~30%,
  office furniture ~25%, furniture & decor ~24% of revenue.
- **Repeat purchase rate is only 3.0%**, and **66.5% of orders** come from
  just 3 states (SP/RJ/MG) — retention and geographic expansion are the
  growth levers.
- Peak month: **Nov 2017** — 7,289 orders, R$987,765 revenue.

## Recommendations

1. **Fix the long-haul lanes first** (MA/CE/BA): renegotiate carriers or
   add regional fulfillment — every late order costs ~1.7 review stars.
2. **Promote split payments on high baskets** (installments already scale
   naturally with basket size) to lift conversion.
3. **Set category-aware free-shipping thresholds** — bulky categories lose
   a quarter of revenue to freight.
4. **Launch retention/win-back campaigns**: a 3% repeat rate on 93k
   customers is the cheapest growth available.
5. **Expand beyond SP/RJ/MG** and investigate the 1-star-heavy categories
   (office furniture: 20.3% one-star reviews).

## Dashboard

`dashboard/olist_dashboard.html` is the finished, interactive dashboard —
open it in any browser (loads plotly.js from CDN). Three pages: Executive Overview,
Delivery & Satisfaction, Products & Margins. Regenerate it any time with:

```bash
python python/build_dashboard.py
```

To rebuild it in Power BI Desktop instead, follow `powerbi/POWERBI_GUIDE.md`.

## Reproduce

```bash
python python/download_data.py      # fetch raw data
python python/build_notebook.py     # clean + build notebook + fact table
# then run sql/01_schema.sql → 02 → 03 in PostgreSQL, or open the notebook
```

## Author

Adnan Habib — entry-level Data Analyst
(SQL · Python · Power BI · Excel)
