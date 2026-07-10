import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="WC 2026 Pro Predictor", layout="wide")
df = pd.read_csv('echipe.csv')

st.title("🏆 WC 2026: Motor de Analiză Sportivă")

col_a, col_b = st.columns([1, 2])

with col_a:
    st.sidebar.header("Parametri Meci")
    t1_name = st.selectbox("Echipa Gazdă", df['Echipa'].unique())
    t2_name = st.selectbox("Echipa Oaspete", df['Echipa'].unique())
    run_sim = st.button("RULARE SIMULARE AVANSATĂ")

t1 = df[df['Echipa'] == t1_name].iloc[0]
t2 = df[df['Echipa'] == t2_name].iloc[0]

with col_b:
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=[t1['Forta_Atac'], t1['Forta_Aparare'], t1['Valoare_Lot_Mil']/10], theta=['Atac', 'Aparare', 'Valoare'], fill='toself', name=t1_name))
    fig.add_trace(go.Scatterpolar(r=[t2['Forta_Atac'], t2['Forta_Aparare'], t2['Valoare_Lot_Mil']/10], theta=['Atac', 'Aparare', 'Valoare'], fill='toself', name=t2_name))
    st.plotly_chart(fig)

if run_sim:
    sims = 1000
    t1_wins = sum([1 for _ in range(sims) if np.random.normal(t1['Forta_Atac'], 5) > np.random.normal(t2['Forta_Atac'], 5)])
    
    prob1 = (t1_wins / sims) * 100
    st.subheader(f"Rezultat: {t1_name} {prob1:.1f}% vs {t2_name} {100-prob1:.1f}%")
    
    col1, col2 = st.columns(2)
    col1.metric(t1['Golgheter'], f"{t1['Prob_Gol']}% șanse gol")
    col2.metric(t2['Golgheter'], f"{t2['Prob_Gol']}% șanse gol")
    
    st.success("Analiză finalizată. Succes pe bilet!")

st.sidebar.divider()
st.sidebar.warning("Abonare VIP: [LINK TELEGRAM]")
