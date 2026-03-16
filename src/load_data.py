import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from db_connect import get_connection

# Load CSV
df = pd.read_csv('../data/sqlinjection_dataset.csv')
df.columns = ['query', 'label']
df = df.dropna()

print(f"Loading {len(df)} rows into database...")

conn = get_connection()
cur = conn.cursor()

# Determine attack type based on query content
def get_attack_type(query):
    query_lower = str(query).lower()
    if 'union' in query_lower:
        return 'union_based'
    elif 'or 1=1' in query_lower or "or '1'='1'" in query_lower:
        return 'tautology'
    elif '--' in query_lower or '#' in query_lower:
        return 'comment_injection'
    elif 'char(' in query_lower:
        return 'char_encoding'
    elif 'sleep' in query_lower or 'benchmark' in query_lower:
        return 'time_based'
    elif 'drop' in query_lower or 'delete' in query_lower:
        return 'destructive'
    else:
        return 'other'

# Insert rows in batches
batch_size = 1000
total = 0

for i in range(0, len(df), batch_size):
    batch = df.iloc[i:i+batch_size]
    for _, row in batch.iterrows():
        attack_type = get_attack_type(row['query']) if row['label'] == 1 else 'none'
        cur.execute("""
            INSERT INTO training_dataset 
            (sample_query, label, attack_type, source)
            VALUES (%s, %s, %s, %s)
        """, (
            str(row['query']),
            bool(row['label']),
            attack_type,
            'kaggle_sqli_dataset'
        ))
    conn.commit()
    total += len(batch)
    print(f"  Loaded {total}/{len(df)} rows...")

print(f"\n✅ Done! {total} rows loaded into training_dataset table.")
cur.close()
conn.close()