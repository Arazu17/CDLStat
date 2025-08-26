import pandas as pd
import sqlite3

# Load Excel
df = pd.read_excel("CDLBO6Stats.xlsx", sheet_name="Sheet1")

# Connect to your existing DB (or create if not exists)
conn = sqlite3.connect("CDLBO6StatsDB.db")

# Write to table
df.to_sql("cdl_stats", conn, if_exists="replace", index=False)

conn.close()
print("✅ Data imported into CDLBO6StatsDB.db, table: cdl_stats")

