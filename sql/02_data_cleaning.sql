-- ============================================================
-- 02_data_cleaning.sql — Olist E-Commerce: data quality fixes
-- Every rule below was found during profiling; each fix is
-- documented with its rationale. Run after 01_schema.sql.
-- Cleaning creates *_clean tables so raw data is never mutated.
-- ============================================================

-- ---------- 1. ORDERS ----------
-- Issue A: 166 orders have order_delivered_carrier_date EARLIER than
-- the purchase timestamp (logistics logging error). The carrier date
-- is unreliable for these rows -> set to NULL, keep the order.
-- Issue B: NULLs in approved/delivered dates are legitimate
-- (canceled / in-flight orders), keep as-is.
DROP TABLE IF EXISTS orders_clean;
CREATE TABLE orders_clean AS
SELECT
    order_id,
    customer_id,
    order_status,
    order_purchase_timestamp,
    order_approved_at,
    CASE
        WHEN order_delivered_carrier_date < order_purchase_timestamp THEN NULL
        ELSE order_delivered_carrier_date
    END AS order_delivered_carrier_date,
    order_delivered_customer_date,
    order_estimated_delivery_date,
    -- derived flags used across the analysis
    CASE
        WHEN order_delivered_customer_date IS NOT NULL
         AND order_delivered_customer_date > order_estimated_delivery_date
        THEN TRUE ELSE FALSE
    END AS is_late_delivery,
    CASE
        WHEN order_delivered_customer_date IS NOT NULL
        THEN (order_delivered_customer_date::date - order_purchase_timestamp::date)
    END AS delivery_days
FROM orders;

-- ---------- 2. REVIEWS ----------
-- Issue: 814 duplicate review_id values (547 orders have >1 review row).
-- Rule: keep the LATEST review per review_id (most recent
-- review_creation_date), which reflects the customer's final opinion.
DROP TABLE IF EXISTS reviews_clean;
CREATE TABLE reviews_clean AS
SELECT DISTINCT ON (review_id)
    review_id, order_id, review_score,
    review_comment_title, review_comment_message,
    review_creation_date, review_answer_timestamp
FROM reviews
ORDER BY review_id, review_creation_date DESC NULLS LAST;

-- ---------- 3. PAYMENTS ----------
-- Issue: 9 payment rows have payment_value <= 0 (invalid).
-- Rule: exclude them; they cannot represent real money movement.
DROP TABLE IF EXISTS payments_clean;
CREATE TABLE payments_clean AS
SELECT *
FROM payments
WHERE payment_value > 0;

-- ---------- 4. PRODUCTS ----------
-- Issue: 610 products have NULL category + name/description metrics;
-- 2 products miss dimension values.
-- Rule: label missing categories 'unknown' (keeps rows for revenue
-- math); leave dimensions NULL (a missing measurement is not zero).
DROP TABLE IF EXISTS products_clean;
CREATE TABLE products_clean AS
SELECT
    product_id,
    COALESCE(product_category_name, 'unknown') AS product_category_name,
    product_name_lenght,
    product_description_lenght,
    product_photos_qty,
    product_weight_g,
    product_length_cm,
    product_height_cm,
    product_width_cm
FROM products;

-- ---------- 5. Validation checks (should all return 0) ----------
-- Orphan order_items after cleaning
SELECT COUNT(*) AS orphan_items
FROM order_items i
LEFT JOIN orders_clean o ON i.order_id = o.order_id
WHERE o.order_id IS NULL;

-- Negative prices / freight (invalid money)
SELECT COUNT(*) AS bad_money
FROM order_items
WHERE price <= 0 OR freight_value < 0;

-- Reviews with scores outside 1-5
SELECT COUNT(*) AS bad_scores
FROM reviews_clean
WHERE review_score NOT BETWEEN 1 AND 5;
