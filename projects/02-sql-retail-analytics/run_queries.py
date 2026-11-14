"""Executes every query in analysis_queries.sql against superstore.db
and writes each result to outputs/Q<n>_<slug>.csv"""
import sqlite3, re, pandas as pd, pathlib

sql = pathlib.Path("analysis_queries.sql").read_text()
queries = [q.strip() for q in sql.split(";") if "SELECT" in q.upper()]
titles = re.findall(r"-- (Q\d+)\. (.+)", sql)
con = sqlite3.connect("superstore.db")
pathlib.Path("outputs").mkdir(exist_ok=True)
for (qid, title), q in zip(titles, queries):
    df = pd.read_sql(q, con)
    slug = re.sub(r"[^a-z0-9]+", "_", title.lower())[:40].strip("_")
    df.to_csv(f"outputs/{qid}_{slug}.csv", index=False)
    print(f"\n=== {qid}. {title} ===")
    print(df.head(10).to_string(index=False))
con.close()
