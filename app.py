import streamlit as st
import pandas as pd

st.set_page_config(page_title="WC 2026 xG Predictor", layout="centered")
df = pd.read_csv('echipe.csv')

st.title("⚽ WC 2026: Goluri Așteptate (xG)")

col1, col2 = st.columns(2)
t1_name = col1.selectbox("Echipa Gazdă", df['Echipa'].unique())
t2_name = col2.selectbox("Echipa Oaspete", df['Echipa'].unique())

if st.button("CALCULEAZA xG 📊"):
    t1 = df[df['Echipa'] == t1_name].iloc[0]
    t2 = df[df['Echipa'] == t2_name].iloc[0]
    
    # Calcul xG
    total_goals = ((t1['Med_Marcate'] + t2['Med_Primite']) / 2) + ((t2['Med_Marcate'] + t1['Med_Primite']) / 2)
    
    st.metric(label="Total Goluri Așteptate (xG)", value=f"{total_goals:.2f}")
    
    if total_goals > 2.5:
        st.success("Predicție: PESTE 2.5 Goluri")
    else:
        st.info("Predicție: SUB 2.5 Goluri")

st.divider()
st.warning("Ponturi VIP pentru Sferturi: [CLICK AICI]")
