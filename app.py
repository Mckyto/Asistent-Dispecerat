import streamlit as st
import pandas as pd

st.set_page_config(page_title="WC 2026 Pro-Predictor", layout="centered")
df = pd.read_csv('echipe.csv')

st.title("⚽ WC 2026: Motor de Analiză Avansată")

col1, col2 = st.columns(2)
lista_echipe = df['Echipa'].unique()
t1_name = col1.selectbox("Echipa 1", lista_echipe)
t2_name = col2.selectbox("Echipa 2", lista_echipe)

if st.button("CALCULEAZA VERDICT PRO"):
    if t1_name == t2_name:
        st.error("Alege echipe diferite!")
    else:
        t1 = df[df['Echipa'] == t1_name].iloc[0]
        t2 = df[df['Echipa'] == t2_name].iloc[0]
        
        # Algoritm cu Ponderare de Formă
        # 1. Ajustăm atacul și apărarea prin Factorul de Formă
        atk1 = t1['Forta_Atac'] * t1['Factor_Forma']
        atk2 = t2['Forta_Atac'] * t2['Factor_Forma']
        def1 = t1['Forta_Aparare'] * t1['Factor_Forma']
        def2 = t2['Forta_Aparare'] * t2['Factor_Forma']
        
        # 2. Calcul goluri cu ajustare dinamică
        goluri_t1 = (t1['Med_Marcate'] * (atk1/90)) + (t2['Med_Primite'] * (def2/90))
        goluri_t2 = (t2['Med_Marcate'] * (atk2/90)) + (t1['Med_Primite'] * (def1/90))
        
        scor1, scor2 = round(goluri_t1/1.2), round(goluri_t2/1.2)
        
        st.subheader(f"Scor estimat: {t1_name} {scor1} - {scor2} {t2_name}")
        
        total = scor1 + scor2
        st.divider()
        # Logica predictiva imbunatatita
        if total >= 2.5:
            st.success(f"Verdict: PESTE 2.5 Goluri (Total: {total})")
        else:
            st.info(f"Verdict: SUB 2.5 Goluri (Total: {total})")

st.divider()
st.warning("Ponturi VIP pentru Sferturi: [CLICK AICI]")
