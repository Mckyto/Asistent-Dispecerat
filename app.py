import streamlit as st
import pandas as pd

st.set_page_config(page_title="WC 2026 Form Predictor", layout="centered")
df = pd.read_csv('echipe.csv')

st.title("⚽ WC 2026: Predictor bazat pe Formă")

col1, col2 = st.columns(2)
t1_name = col1.selectbox("Echipa 1", df['Echipa'].unique())
t2_name = col2.selectbox("Echipa 2", df['Echipa'].unique())

if st.button("CALCULEAZA CU DATE REALE"):
    t1 = df[df['Echipa'] == t1_name].iloc[0]
    t2 = df[df['Echipa'] == t2_name].iloc[0]
    
    # Logică de calcul bazată pe forma turneului
    # Se ponderează golurile marcate cu forța de atac actuală
    goluri_t1 = (t1['Med_Marcate'] * (t1['Forta_Atac']/85)) + (t2['Med_Primite'] * (t2['Forta_Aparare']/85))
    goluri_t2 = (t2['Med_Marcate'] * (t2['Forta_Atac']/85)) + (t1['Med_Primite'] * (t1['Forta_Aparare']/85))
    
    scor1, scor2 = round(goluri_t1/2), round(goluri_t2/2)
    
    st.subheader(f"Scor estimat: {t1_name} {scor1} - {scor2} {t2_name}")
    
    total = scor1 + scor2
    st.divider()
    if total >= 2.5:
        st.success(f"Verdict: PESTE 2.5 Goluri (Total: {total})")
    else:
        st.info(f"Verdict: SUB 2.5 Goluri (Total: {total})")

st.divider()
st.warning("Ponturi VIP pentru Sferturi: [CLICK AICI]")
