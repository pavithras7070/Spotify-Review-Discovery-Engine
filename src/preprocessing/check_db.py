import sqlite3
import pandas as pd
conn = sqlite3.connect('data/staging.db')
df = pd.read_sql_query("SELECT * FROM cleaned_reviews LIMIT 5", conn)
print(df)
conn.close()
