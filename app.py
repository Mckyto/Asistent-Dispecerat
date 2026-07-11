import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="WC 2026 Over/Under Predictor", layout="wide")
df = pd.read_csv('echipe.csv')

st.title("⚽ WC 2026: Predictor Goluri (Over/Under)")

col_a, col_b = st.columns([1, 2])

with col_a:
    t1_name = st.selectbox("Echipa Gazdă", df['Echipa'].unique())
    t2_name = st.selectbox("Echipa Oaspete", df['Echipa'].unique())
    run_sim = st.button("CALCULEAZA GOLURI 📊")

t1 = df[df['Echipa'] == t1_name].iloc[0]
t2 = df[df['Echipa'] == t2_name].iloc[0]

if run_sim:
    # Logica de calcul goluri estimate
    # Media atacului echipei 1 vs apararea echipei 2
    xG1 = (t1['Med_Marcate'] + t2['Med_Primite']) / 2
    xG2 = (t2['Med_Marcate'] + t1['Med_Primite']) / 2
    total_goals = xG1 + xG2
    
    with col_b:
        st.subheader(f"Total Goluri Așteptate (xG): {total_goals:.2f}")
        
        if total_goals > 2.5:
            st.metric("Pariu Recomandat", "Peste 2.5 Goluri", delta="Probabilitate Ridicată")
        else:
            st.metric("Pariu Recomandat", "Sub 2.5 Goluri", delta="Probabilitate Ridicată")
            
        st.write(f"Scor estimat: {round(xG1)} - {round(xG2)}")

st.sidebar.divider()
st.sidebar.warning("Vrei ponturi Over/Under VIP? [CLICK AICI]")
