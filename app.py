import streamlit as st
import pandas as pd

st.set_page_config(page_title="WC 2026 Pro-Predictor", layout="centered")
df = pd.read_csv('echipe.csv')

st.title("⚽ WC 2026: Verdict & Goluri")

col1, col2 = st.columns(2)
lista_echipe = df['Echipa'].unique()
t1_name = col1.selectbox("Echipa 1", lista_echipe)
t2_name = col2.selectbox("Echipa 2", lista_echipe)

if st.button("CALCULEAZA"):
    t1 = df[df['Echipa'] == t1_name].iloc[0]
    t2 = df[df['Echipa'] == t2_name].iloc[0]
    
    # Calcul scor
    atk1, atk2 = t1['Forta_Atac'] * t1['Factor_Forma'], t2['Forta_Atac'] * t2['Factor_Forma']
    def1, def2 = t1['Forta_Aparare'] * t1['Factor_Forma'], t2['Forta_Aparare'] * t2['Factor_Forma']
    
    scor1 = round((t1['Med_Marcate'] * (atk1/90)) + (t2['Med_Primite'] * (def2/90)) / 1.5)
    scor2 = round((t2['Med_Marcate'] * (atk2/90)) + (t1['Med_Primite'] * (def1/90)) / 1.5)
    
    st.subheader(f"Scor estimat: {t1_name} {scor1} - {scor2} {t2_name}")
    
    # Cine marchează (Echipa cu puterea ofensivă mai mare)
    st.divider()
    prob_gol_t1 = t1['Putere_Ofensiva'] * t1['Factor_Forma']
    prob_gol_t2 = t2['Putere_Ofensiva'] * t2['Factor_Forma']
    
    if prob_gol_t1 > prob_gol_t2:
        st.write(f"👉 Echipa cu probabilitate mai mare să înscrie: **{t1_name}**")
    else:
        st.write(f"👉 Echipa cu probabilitate mai mare să înscrie: **{t2_name}**")
        
    st.divider()
    # Logica Calificare
    if scor1 > scor2:
        st.success(f"🏆 Calificată: {t1_name}")
    elif scor2 > scor1:
        st.success(f"🏆 Calificată: {t2_name}")
    else:
        winner = t1_name if t1['Experienta_Penalti'] > t2['Experienta_Penalti'] else t2_name
        st.warning(f"Egalitate! După penalty-uri, merge mai departe: **{winner}**")

st.sidebar.warning("Ponturi VIP: [LINK TELEGRAM]")
