"""Download the Olist Brazilian E-Commerce public dataset.

Source: https://github.com/olist/work-at-olist-data (CC BY-SA 4.0)
~100k orders from 2016-2018. Run from the project root.
"""
import os
import urllib.request

BASE = "https://raw.githubusercontent.com/olist/work-at-olist-data/master/datasets/"
FILES = [
    "olist_customers_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_orders_dataset.csv",
    "olist_products_dataset.csv",
    "olist_sellers_dataset.csv",
    "product_category_name_translation.csv",
]

os.makedirs("data/raw", exist_ok=True)
for f in FILES:
    dest = os.path.join("data/raw", f)
    if os.path.exists(dest):
        print(f"exists, skipping: {f}")
        continue
    print(f"downloading: {f}")
    urllib.request.urlretrieve(BASE + f, dest)
print("done")
