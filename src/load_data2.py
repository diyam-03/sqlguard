import pandas as pd
import sys
import os
sys.path.insert(0, '.')
from src.db_connect import get_connection

# Load CSV
df = pd.read_csv('data/sqlinjection_dataset2.csv')
print(f"Dataset shape: {df.shape}")

# Clean up
df = df.dropna(subset=['Query', 'Type Attack'])
df['label'] = df['Type Attack'].apply(lambda x: True if x == 'Malicious' else False)

def get_attack_type(query, label):
    if not label:
        return 'none'
    q = str(query).lower()
    if 'union' in q:
        return 'union_based'
    elif 'or 1=1' in q or "or '1'='1'" in q:
        return 'tautology'
    elif '--' in q or '#' in q:
        return 'comment_injection'
    elif 'char(' in q:
        return 'char_encoding'
    elif 'sleep' in q:
        return 'time_based'
    elif 'drop' in q or 'delete' in q:
        return 'destructive'
    else:
        return 'other'

conn = get_connection()
cur = conn.cursor()

batch_size = 5000
total = 0

print(f"Loading {len(df)} rows...")

for i in range(0, len(df), batch_size):
    batch = df.iloc[i:i+batch_size]
    for _, row in batch.iterrows():
        attack_type = get_attack_type(row['Query'], row['label'])
        cur.execute("""
            INSERT INTO training_dataset 
            (sample_query, label, attack_type, source)
            VALUES (%s, %s, %s, %s)
        """, (
            str(row['Query']),
            bool(row['label']),
            attack_type,
            'mendeley_sqli_dataset'
        ))
    conn.commit()
    total += len(batch)
    print(f"  Loaded {total}/{len(df)} rows...")

print(f"\n✅ Done! {total} rows loaded.")
cur.close()
conn.close()