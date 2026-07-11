import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title="WC 2026 Scor Predictor", layout="centered")
df = pd.read_csv('echipe.csv')

st.title("⚽ WC 2026: Verdict & Scor")

col1, col2 = st.columns(2)
t1_name = col1.selectbox("Echipa 1", df['Echipa'].unique())
t2_name = col2.selectbox("Echipa 2", df['Echipa'].unique())

if st.button("GENEREAZA VERDICT"):
    t1 = df[df['Echipa'] == t1_name].iloc[0]
    t2 = df[df['Echipa'] == t2_name].iloc[0]
    
    # Calcul scor estimativ (rotunjit la cel mai apropiat întreg)
    goluri_t1 = round((t1['Med_Marcate'] + t2['Med_Primite']) / 2)
    goluri_t2 = round((t2['Med_Marcate'] + t1['Med_Primite']) / 2)
    
    # Afișare Scor
    st.subheader(f"Scor estimat: {t1_name} {goluri_t1} - {goluri_t2} {t2_name}")
    
    st.divider()
    
    # Verdict Peste/Sub
    total = goluri_t1 + goluri_t2
    if total > 2.5:
        st.success("Verdict: PESTE 2.5 Goluri")
    else:
        st.info("Verdict: SUB 2.5 Goluri")

st.divider()
st.warning("Ponturi VIP pentru Sferturi: [CLICK AICI]")
