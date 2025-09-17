# src/ingest.py
import pandas as pd
from pathlib import Path
from .etl import clean_and_normalize, simple_indicators, load_to_db
from .db import init_db

def ingest_csv(path: str):
    init_db()
    df = pd.read_csv(path)
    dfc = clean_and_normalize(df)
    dfi = simple_indicators(dfc)
    load_to_db(dfi)
    print(f"Ingested {len(dfi)} records from {path}")

if __name__ == "__main__":
    import sys
    p = sys.argv[1] if len(sys.argv) > 1 else "../sample_data/sample_nutrition.csv"
    ingest_csv(p)
