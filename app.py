import streamlit as st
import pandas as pd

df = pd.read_csv('echipe.csv')

st.title("🏆 WC 2026: Predictor Goluri & Scor")

col1, col2 = st.columns(2)
team1 = col1.selectbox("Echipa A", df['Echipa'].unique())
team2 = col2.selectbox("Echipa B", df['Echipa'].unique())

if st.button("GENEREAZA PONTURI ⚽"):
    t1 = df[df['Echipa'] == team1].iloc[0]
    t2 = df[df['Echipa'] == team2].iloc[0]
    
    # Predictie scor (simplificata)
    goluri1 = int((t1['Forta_Atac'] / 20))
    goluri2 = int((t2['Forta_Atac'] / 20))
    
    st.subheader(f"Predictie Scor Final: {goluri1} - {goluri2}")
    
    # Predictie jucator
    st.write(f"---")
    st.write(f"🎯 **Jucător cheie să marcheze:**")
    st.write(f"👉 {t1['Golgheter']} ({t1['Prob_Gol']}% șanse)")
    st.write(f"👉 {t2['Golgheter']} ({t2['Prob_Gol']}% șanse)")
    
    st.divider()
    st.warning("Pont pariu: GG (Ambele înscriu) - Probabilitate Ridicată")
