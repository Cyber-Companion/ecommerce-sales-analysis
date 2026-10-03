# Power BI Dashboard — Build Guide

Import **`fact_orders_clean.csv`** (112,650 rows × 18 cols, one row per
order item, already cleaned). In Power BI Desktop: **Get Data → Text/CSV**,
then set types: `order_purchase_timestamp` → Date/Time,
`delivery_days` → Whole Number, `is_late_delivery` → True/False,
`price`/`freight_value` → Decimal.

Suggested: 3 pages. All filters should respect a **Year–Month slicer**
(built from `order_purchase_timestamp`) and an **order_status slicer**
(default to `delivered`).

---

## Page 1 — Executive Overview

**KPI cards:** Delivered Revenue · Delivered Orders · AOV · Avg Review Score

**Visuals**
- Line chart: Delivered Revenue by Year–Month (trend)
- Bar chart: Revenue by `category_en` (Top 10)
- Donut: Orders by `payment_type`
- Filled map: Orders by `customer_state`

## Page 2 — Delivery & Satisfaction

**KPI cards:** Late Delivery % · Avg Delivery Days · Avg Review (late vs on-time)

**Visuals**
- Bar chart: Late % by `customer_state` (highlights MA/CE/BA problem lanes)
- Histogram / column: distribution of `delivery_days`
- Clustered column: Avg `review_score` by `is_late_delivery`
- Table: worst lanes — state, late %, avg delivery days

## Page 3 — Products & Margins

**Visuals**
- Table: category, revenue, orders, freight burden % (use DAX below)
- Bar chart: Freight burden % by `category_en` (Top 10)
- Bar chart: Avg `review_score` by `category_en` (Bottom 10 → quality issues)
- Table: seller leaderboard — `seller_id`, orders, revenue, avg review
  (filter: orders ≥ 50)

---

## DAX measures (create in Modeling → New Measure)

```dax
Delivered Revenue =
CALCULATE ( SUM ( fact_orders_clean[price] ),
            fact_orders_clean[order_status] = "delivered" )

Delivered Orders =
CALCULATE ( DISTINCTCOUNT ( fact_orders_clean[order_id] ),
            fact_orders_clean[order_status] = "delivered" )

AOV = DIVIDE ( [Delivered Revenue], [Delivered Orders] )

Late Delivery % =
DIVIDE (
    CALCULATE ( COUNTROWS ( fact_orders_clean ),
                fact_orders_clean[is_late_delivery] = TRUE(),
                fact_orders_clean[order_status] = "delivered" ),
    [Delivered Orders]
)

Avg Delivery Days =
CALCULATE ( AVERAGE ( fact_orders_clean[delivery_days] ),
            fact_orders_clean[order_status] = "delivered" )

Avg Review Score = AVERAGE ( fact_orders_clean[review_score] )

Freight Burden % =
DIVIDE ( SUM ( fact_orders_clean[freight_value] ),
         SUM ( fact_orders_clean[price] ) )
```

**Year–Month column** (for the trend slicer), Modeling → New Column:

```dax
Year-Month = FORMAT ( fact_orders_clean[order_purchase_timestamp], "YYYY-MM" )
```

## Publish

Power BI Desktop → **Publish** to the Power BI Service, or export the
three pages as PDF. Screenshots of each page also work well in the GitHub
README and on your resume portfolio link.
