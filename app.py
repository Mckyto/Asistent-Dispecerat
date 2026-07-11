import streamlit as st
import pandas as pd

st.set_page_config(page_title="WC 2026 Predictor", layout="centered")
df = pd.read_csv('echipe.csv')

st.title("⚽ WC 2026: Predictor Goluri")

col1, col2 = st.columns(2)
t1_name = col1.selectbox("Echipa 1", df['Echipa'].unique())
t2_name = col2.selectbox("Echipa 2", df['Echipa'].unique())

if st.button("ANALIZEAZA MECIUL"):
    t1 = df[df['Echipa'] == t1_name].iloc[0]
    t2 = df[df['Echipa'] == t2_name].iloc[0]
    
    # Calcul goluri
    total_goals = ((t1['Med_Marcate'] + t2['Med_Primite']) / 2) + ((t2['Med_Marcate'] + t1['Med_Primite']) / 2)
    
    st.metric(label="Goluri estimate pentru acest meci", value=f"{total_goals:.2f}")
    
    if total_goals > 2.5:
        st.success("Verdict: PESTE 2.5 Goluri")
    else:
        st.info("Verdict: SUB 2.5 Goluri")

st.divider()
st.warning("Ponturi VIP pentru Sferturi: [CLICK AICI]")
