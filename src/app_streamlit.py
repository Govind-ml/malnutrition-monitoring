# src/app_streamlit.py
import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
import plotly.express as px

DB_PATH = Path(__file__).resolve().parents[1] / "malnutrition.db"

@st.cache_data
def load_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM child_records", conn, parse_dates=['record_date'])
    conn.close()
    return df

st.set_page_config(page_title="Malnutrition Monitor", layout="wide")
st.title("Real-Time Malnutrition Monitoring — Prototype")

df = load_data()
if df.empty:
    st.warning("No records in DB. Run `python src/ingest.py sample_data/sample_nutrition.csv` to ingest sample data.")
else:
    st.markdown("### Latest data summary")
    # compute aggregated rates by state
    agg = df.groupby('state').agg(
        total=('child_id','count'),
        wasted = ('wasted','sum'),
        underweight = ('underweight','sum'),
        stunted = ('stunted','sum')
    ).reset_index()
    for col in ['wasted','underweight','stunted']:
        agg[f'{col}_rate'] = (agg[col] / agg['total']) * 100

    st.dataframe(agg)

    st.markdown("### Map / Trend (example)")
    # simple bar of wasted rate
    fig = px.bar(agg.sort_values('wasted_rate', ascending=False),
                 x='state', y='wasted_rate',
                 labels={'wasted_rate':'Wasting (%)','state':'State'}, title='Wasting rate by state')
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Records (last 50)")
    st.dataframe(df.sort_values('record_date', ascending=False).head(50))
