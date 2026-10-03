-- ============================================================
-- 03_analysis.sql — Olist E-Commerce: business analysis
-- Run after 01_schema.sql and 02_data_cleaning.sql.
-- All revenue figures use DELIVERED orders only (recognized revenue).
-- ============================================================

-- ---------- Q1. Headline KPIs ----------
WITH delivered AS (
    SELECT
        o.order_id,
        c.customer_unique_id,
        SUM(i.price)         AS revenue,
        SUM(i.freight_value) AS freight
    FROM orders_clean o
    JOIN customers c   ON o.customer_id = c.customer_id
    JOIN order_items i ON o.order_id = i.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY o.order_id, c.customer_unique_id
)
SELECT
    COUNT(*)                              AS delivered_orders,
    COUNT(DISTINCT customer_unique_id)    AS unique_customers,
    ROUND(SUM(revenue), 0)                AS total_revenue_brl,
    ROUND(SUM(freight), 0)                AS total_freight_brl,
    ROUND(AVG(revenue), 2)                AS avg_order_value_brl,
    (SELECT COUNT(DISTINCT i.seller_id)
     FROM order_items i
     JOIN orders_clean o ON i.order_id = o.order_id
     WHERE o.order_status = 'delivered')  AS active_sellers
FROM delivered;

-- ---------- Q2. Monthly revenue & order trend (with MoM growth) ----------
WITH monthly AS (
    SELECT
        DATE_TRUNC('month', o.order_purchase_timestamp)::date AS month,
        COUNT(DISTINCT o.order_id) AS orders,
        SUM(i.price)              AS revenue
    FROM orders_clean o
    JOIN order_items i ON o.order_id = i.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY 1
)
SELECT
    month,
    orders,
    ROUND(revenue, 0) AS revenue_brl,
    ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY month))
          / NULLIF(LAG(revenue) OVER (ORDER BY month), 0), 1) AS mom_growth_pct
FROM monthly
ORDER BY month;

-- ---------- Q3. Top 10 product categories by revenue (bottom 5 too) ----------
SELECT
    COALESCE(t.product_category_name_english, p.product_category_name) AS category,
    COUNT(DISTINCT i.order_id) AS orders,
    ROUND(SUM(i.price), 0)      AS revenue_brl,
    ROUND(AVG(i.price), 2)      AS avg_item_price_brl
FROM order_items i
JOIN orders_clean o ON i.order_id = o.order_id
JOIN products_clean p ON i.product_id = p.product_id
LEFT JOIN category_translation t
       ON p.product_category_name = t.product_category_name
WHERE o.order_status = 'delivered'
GROUP BY 1
ORDER BY revenue_brl DESC
LIMIT 10;

-- ---------- Q4. Delivery performance: how late, and where ----------
SELECT
    COUNT(*) AS delivered_orders,
    ROUND(AVG(delivery_days), 1) AS avg_delivery_days,
    SUM(CASE WHEN is_late_delivery THEN 1 ELSE 0 END) AS late_orders,
    ROUND(100.0 * SUM(CASE WHEN is_late_delivery THEN 1 ELSE 0 END)
          / COUNT(*), 1) AS late_pct
FROM orders_clean
WHERE order_status = 'delivered'
  AND delivery_days IS NOT NULL;

-- Late-delivery rate by customer state (min 500 delivered orders)
SELECT
    c.customer_state AS state,
    COUNT(*) AS delivered_orders,
    ROUND(100.0 * SUM(CASE WHEN o.is_late_delivery THEN 1 ELSE 0 END)
          / COUNT(*), 1) AS late_pct,
    ROUND(AVG(o.delivery_days), 1) AS avg_delivery_days
FROM orders_clean o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_status = 'delivered' AND o.delivery_days IS NOT NULL
GROUP BY 1
HAVING COUNT(*) >= 500
ORDER BY late_pct DESC;

-- ---------- Q5. Does late delivery hurt satisfaction? ----------
SELECT
    o.is_late_delivery,
    COUNT(r.review_score)            AS reviews,
    ROUND(AVG(r.review_score), 2)    AS avg_review_score,
    ROUND(100.0 * SUM(CASE WHEN r.review_score = 1 THEN 1 ELSE 0 END)
          / COUNT(*), 1)             AS pct_1_star
FROM orders_clean o
JOIN reviews_clean r ON o.order_id = r.order_id
WHERE o.order_status = 'delivered'
GROUP BY 1;

-- ---------- Q6. Payment mix & installment behavior ----------
SELECT
    payment_type,
    COUNT(*) AS payments,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct_of_payments,
    ROUND(AVG(payment_installments), 1) AS avg_installments,
    ROUND(AVG(payment_value), 2)         AS avg_payment_value_brl
FROM payments_clean
GROUP BY 1
ORDER BY payments DESC;

-- Installments rise with basket size: evidence for a "split payment" nudge
SELECT
    CASE
        WHEN order_value < 100 THEN 'under 100'
        WHEN order_value < 300 THEN '100-300'
        ELSE '300+'
    END AS basket_band_brl,
    COUNT(*) AS orders,
    ROUND(AVG(installments), 1) AS avg_installments
FROM (
    SELECT order_id, SUM(payment_value) AS order_value,
           MAX(payment_installments) AS installments
    FROM payments_clean
    GROUP BY order_id
) p
GROUP BY 1
ORDER BY 1;

-- ---------- Q7. Review score distribution & worst categories ----------
SELECT
    review_score,
    COUNT(*) AS reviews,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
FROM reviews_clean
GROUP BY 1
ORDER BY 1;

-- Categories with the highest share of 1-star reviews (min 200 reviews)
SELECT
    COALESCE(t.product_category_name_english, p.product_category_name) AS category,
    COUNT(*) AS reviews,
    ROUND(100.0 * SUM(CASE WHEN r.review_score = 1 THEN 1 ELSE 0 END)
          / COUNT(*), 1) AS pct_1_star
FROM reviews_clean r
JOIN orders_clean o ON r.order_id = o.order_id
JOIN order_items i  ON o.order_id = i.order_id
JOIN products_clean p ON i.product_id = p.product_id
LEFT JOIN category_translation t
       ON p.product_category_name = t.product_category_name
GROUP BY 1
HAVING COUNT(*) >= 200
ORDER BY pct_1_star DESC
LIMIT 10;

-- ---------- Q8. Customer concentration & repeat purchase rate ----------
-- Share of delivered orders from the top 3 states
WITH state_orders AS (
    SELECT c.customer_state AS state, COUNT(*) AS orders
    FROM orders_clean o
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
    GROUP BY 1
)
SELECT
    ROUND(100.0 * SUM(CASE WHEN state IN ('SP','RJ','MG') THEN orders ELSE 0 END)
          / SUM(orders), 1) AS top3_states_pct_of_orders
FROM state_orders;

-- Repeat purchase rate (same human customer ordering more than once)
SELECT
    COUNT(*) AS unique_customers,
    SUM(CASE WHEN order_count > 1 THEN 1 ELSE 0 END) AS repeat_customers,
    ROUND(100.0 * SUM(CASE WHEN order_count > 1 THEN 1 ELSE 0 END)
          / COUNT(*), 1) AS repeat_rate_pct
FROM (
    SELECT c.customer_unique_id, COUNT(DISTINCT o.order_id) AS order_count
    FROM orders_clean o
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
    GROUP BY 1
) t;

-- ---------- Q9. Freight burden: where shipping eats the margin ----------
-- Weighted: total freight / total revenue per category (AVG of per-item
-- ratios would overweight cheap items with high shipping).
SELECT
    COALESCE(t.product_category_name_english, p.product_category_name) AS category,
    COUNT(*) AS items,
    ROUND(100.0 * SUM(i.freight_value) / NULLIF(SUM(i.price), 0), 1) AS freight_pct_of_revenue,
    ROUND(AVG(p.product_weight_g), 0) AS avg_weight_g
FROM order_items i
JOIN orders_clean o ON i.order_id = o.order_id
JOIN products_clean p ON i.product_id = p.product_id
LEFT JOIN category_translation t
       ON p.product_category_name = t.product_category_name
WHERE o.order_status = 'delivered'
GROUP BY 1
HAVING COUNT(*) >= 500
ORDER BY freight_pct_of_revenue DESC
LIMIT 10;

-- ---------- Q10. Seller leaderboard: revenue vs. satisfaction ----------
SELECT
    i.seller_id,
    s.seller_state,
    COUNT(DISTINCT i.order_id) AS orders,
    ROUND(SUM(i.price), 0)      AS revenue_brl,
    ROUND(AVG(r.review_score), 2) AS avg_review_score
FROM order_items i
JOIN orders_clean o ON i.order_id = o.order_id
JOIN sellers s      ON i.seller_id = s.seller_id
LEFT JOIN reviews_clean r ON o.order_id = r.order_id
WHERE o.order_status = 'delivered'
GROUP BY 1, 2
HAVING COUNT(DISTINCT i.order_id) >= 50
ORDER BY revenue_brl DESC
LIMIT 15;
