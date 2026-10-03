-- ============================================================
-- 01_schema.sql — Olist E-Commerce: table definitions
-- Dialect: PostgreSQL (also runs on MySQL with minor tweaks,
-- see notes at the bottom). Load raw CSVs into these tables first.
-- Source: https://github.com/olist/work-at-olist-data (CC BY-SA 4.0)
-- ============================================================

DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS sellers;
DROP TABLE IF EXISTS category_translation;

CREATE TABLE customers (
    customer_id            TEXT PRIMARY KEY,
    customer_unique_id     TEXT NOT NULL,
    customer_zip_code_prefix INTEGER,
    customer_city          TEXT,
    customer_state         TEXT
);

CREATE TABLE orders (
    order_id                    TEXT PRIMARY KEY,
    customer_id                 TEXT NOT NULL REFERENCES customers(customer_id),
    order_status                TEXT NOT NULL,
    order_purchase_timestamp    TIMESTAMP NOT NULL,
    order_approved_at           TIMESTAMP,
    order_delivered_carrier_date TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date DATE
);

CREATE TABLE order_items (
    order_id            TEXT NOT NULL REFERENCES orders(order_id),
    order_item_id       INTEGER NOT NULL,
    product_id          TEXT NOT NULL REFERENCES products(product_id),
    seller_id           TEXT NOT NULL REFERENCES sellers(seller_id),
    shipping_limit_date TIMESTAMP,
    price               NUMERIC(10, 2) NOT NULL,
    freight_value       NUMERIC(10, 2) NOT NULL,
    PRIMARY KEY (order_id, order_item_id)
);

CREATE TABLE payments (
    order_id             TEXT NOT NULL REFERENCES orders(order_id),
    payment_sequential   INTEGER NOT NULL,
    payment_type         TEXT NOT NULL,
    payment_installments INTEGER NOT NULL,
    payment_value        NUMERIC(10, 2) NOT NULL
);

CREATE TABLE reviews (
    review_id               TEXT PRIMARY KEY,
    order_id                TEXT NOT NULL REFERENCES orders(order_id),
    review_score            INTEGER NOT NULL CHECK (review_score BETWEEN 1 AND 5),
    review_comment_title    TEXT,
    review_comment_message  TEXT,
    review_creation_date    TIMESTAMP,
    review_answer_timestamp TIMESTAMP
);

CREATE TABLE products (
    product_id               TEXT PRIMARY KEY,
    product_category_name    TEXT,
    product_name_lenght      INTEGER,   -- kept as in source (typo is theirs)
    product_description_lenght INTEGER, -- kept as in source (typo is theirs)
    product_photos_qty       INTEGER,
    product_weight_g         INTEGER,
    product_length_cm        NUMERIC(8, 2),
    product_height_cm        NUMERIC(8, 2),
    product_width_cm         NUMERIC(8, 2)
);

CREATE TABLE sellers (
    seller_id              TEXT PRIMARY KEY,
    seller_zip_code_prefix INTEGER,
    seller_city            TEXT,
    seller_state           TEXT
);

CREATE TABLE category_translation (
    product_category_name         TEXT PRIMARY KEY,
    product_category_name_english TEXT NOT NULL
);

-- ============================================================
-- Load with (PostgreSQL):
--   \copy customers FROM 'data/raw/olist_customers_dataset.csv' CSV HEADER;
--   ... repeat per table ...
-- MySQL notes: replace TIMESTAMP with DATETIME, NUMERIC(10,2) with
-- DECIMAL(10,2), and TEXT PKs are fine on InnoDB (index length OK here).
-- ============================================================
