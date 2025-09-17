# src/etl.py
import pandas as pd
from datetime import datetime
from .db import get_conn
import numpy as np

def clean_and_normalize(df: pd.DataFrame) -> pd.DataFrame:
    # canonicalize column names
    df = df.rename(columns=lambda s: s.strip().lower())
    # keep expected columns, add defaults if missing
    expected = ['child_id','age_months','sex','weight_kg','height_cm','district','state','record_date']
    for c in expected:
        if c not in df.columns:
            df[c] = None
    # convert types
    df['age_months'] = pd.to_numeric(df['age_months'], errors='coerce').fillna(0).astype(int)
    df['weight_kg'] = pd.to_numeric(df['weight_kg'], errors='coerce')
    df['height_cm'] = pd.to_numeric(df['height_cm'], errors='coerce')
    # ensure date
    df['record_date'] = pd.to_datetime(df['record_date'], errors='coerce').fillna(pd.Timestamp.today()).dt.strftime('%Y-%m-%d')
    return df[expected]

def simple_indicators(df: pd.DataFrame) -> pd.DataFrame:
    # Prototype: simple cutoffs (not WHO z-scores). Replace with proper z-score calc later.
    # Wasting: weight-for-height low -> here we'll use BMI proxy (kg / (m^2))
    df = df.copy()
    df['height_m'] = df['height_cm'] / 100.0
    df['bmi'] = df['weight_kg'] / (df['height_m']**2)
    # NOTE: these are illustrative thresholds
    df['wasted'] = np.where(df['bmi'] < 13.5, 1, 0)
    df['underweight'] = np.where(df['weight_kg'] < 10.0, 1, 0)
    # Stunting approx: very short for age (prototype): height_cm < age_months*0.5 + 50 (very rough)
    df['stunted'] = np.where(df['height_cm'] < (df['age_months']*0.5 + 50), 1, 0)
    return df

def load_to_db(df: pd.DataFrame):
    conn = get_conn()
    # keep only the base schema columns
    keep_cols = ['child_id','age_months','sex','weight_kg','height_cm','district','state','record_date']
    df[keep_cols].to_sql('child_records', conn, if_exists='append', index=False)
    conn.close()

