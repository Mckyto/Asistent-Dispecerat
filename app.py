import streamlit as st
import pandas as pd

# Încărcăm datele din sferturi
df = pd.read_csv('echipe.csv')

st.set_page_config(page_title="WC 2026: Predictor Sferturi", layout="centered", page_icon="🏆")

st.title("🏆 WC 2026 Predictor - Faza Eliminatorie")
st.write("Simulări statistice bazate pe valoarea loturilor și performanța actuală în turneu.")

# Secțiune Meciul Zilei
st.info("🔥 **Meciul Zilei (10 Iulie): Spania vs. Belgia**")

# Selectoare meci
col1, col2 = st.columns(2)
team1 = col1.selectbox("Echipa Gazdă", df['Echipa'].unique(), index=2) # Default Spania
team2 = col2.selectbox("Echipa Oaspete", df['Echipa'].unique(), index=3) # Default Belgia

if st.button("RUN SIMULATION 📊"):
    t1_data = df[df['Echipa'] == team1].iloc[0]
    t2_data = df[df['Echipa'] == team2].iloc[0]
    
    # Algoritm de calcul pentru meciuri cu miză uriașă
    score1 = (t1_data['Forta_Atac'] * 0.5) + (t1_data['Forta_Aparare'] * 0.5)
    score2 = (t2_data['Forta_Atac'] * 0.5) + (t2_data['Forta_Aparare'] * 0.5)
    
    total = score1 + score2
    prob1 = (score1 / total) * 100
    prob2 = 100 - prob1
    
    st.subheader("📊 Rezultatul Simulării:")
    
    c1, c2 = st.columns(2)
    c1.metric(label=f"Șanse Calificare {team1}", value=f"{prob1:.1f}%")
    c2.metric(label=f"Șanse Calificare {team2}", value=f"{prob2:.1f}%")
    
    st.divider()
    castigator = team1 if prob1 > prob2 else team2
    st.success(f"Modelul statistic indică victoria echipei: **{castigator}**")

st.divider()
st.warning("⚠️ **Vrei cotele VIP și ponturi pentru pariuri live la Spania vs Belgia?** Alătură-te comunității noastre de Telegram acum! [Click aici pentru acces gratuit]")
