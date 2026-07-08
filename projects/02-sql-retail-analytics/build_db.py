"""Builds a normalized SQLite database (superstore.db) from the raw Superstore CSV.
Splits the flat file into customers / products / orders / order_items tables."""
import pandas as pd, sqlite3

df = pd.read_csv("superstore.csv")
df.columns = [c.strip().replace(" ", "_").replace("-", "_").lower() for c in df.columns]
df = df.dropna(subset=["order_date", "ship_date"])  # drop malformed rows
df = df[pd.to_datetime(df["order_date"], errors="coerce").notna()]
df["order_date"] = pd.to_datetime(df["order_date"]).dt.date
df["ship_date"] = pd.to_datetime(df["ship_date"]).dt.date

con = sqlite3.connect("superstore.db")
customers = df[["customer_id", "customer_name", "segment"]].drop_duplicates("customer_id")
products = df[["product_id", "product_name", "category", "sub_category"]].drop_duplicates("product_id")
orders = df[["order_id", "order_date", "ship_date", "ship_mode", "customer_id", "city", "state", "region", "postal_code"]].drop_duplicates("order_id")
items = df[["order_id", "product_id", "sales", "quantity", "discount", "profit"]]
for name, t in [("customers", customers), ("products", products), ("orders", orders), ("order_items", items)]:
    t.to_sql(name, con, index=False, if_exists="replace")
con.executescript("""
CREATE INDEX IF NOT EXISTS ix_items_order ON order_items(order_id);
CREATE INDEX IF NOT EXISTS ix_orders_cust ON orders(customer_id);
""")
print({n: pd.read_sql(f"SELECT COUNT(*) n FROM {n}", con)["n"][0] for n in ["customers","products","orders","order_items"]})
con.close()
