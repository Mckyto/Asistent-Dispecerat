import streamlit as st
import pandas as pd

# Încarcăm datele
df = pd.read_csv('echipe.csv')

st.set_page_config(page_title="WC 2026 Predictor", layout="centered")
st.title("⚽ WC 2026: Predictor de Șanse")

col1, col2 = st.columns(2)
team1 = col1.selectbox("Echipa A", df['Echipa'])
team2 = col2.selectbox("Echipa B", df['Echipa'])

if st.button("CALCULEAZA ȘANSELE ACUM"):
    t1 = df[df['Echipa'] == team1].iloc[0]
    t2 = df[df['Echipa'] == team2].iloc[0]
    
    score1 = (t1['Forta_Atac'] * 0.6) + (t1['Forta_Aparare'] * 0.4)
    score2 = (t2['Forta_Atac'] * 0.6) + (t2['Forta_Aparare'] * 0.4)
    
    prob1 = (score1 / (score1 + score2)) * 100
    prob2 = 100 - prob1
    
    st.metric(label=f"Probabilitate {team1}", value=f"{prob1:.1f}%")
    st.metric(label=f"Probabilitate {team2}", value=f"{prob2:.1f}%")
    
    st.divider()
    st.warning("Vrei să pariezi sau să afli tactica câștigătoare? Intră pe grupul nostru VIP pentru analize detaliate!")
