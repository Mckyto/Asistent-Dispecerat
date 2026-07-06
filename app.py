import streamlit as st
import numpy as np
import json

# Încărcare date
try:
    with open("loturi.json", "r", encoding="utf-8") as f:
        date_echipe = json.load(f)
except:
    st.error("Eroare la încărcarea fișierului loturi.json!")
    st.stop()

st.title("⚽ AI Scorecast Pro")

col1, col2 = st.columns(2)
with col1:
    e1 = st.selectbox("Echipa 1", list(date_echipe.keys()), key="e1")
    t1 = st.multiselect("Titulari E1", date_echipe[e1], format_func=lambda x: x['nume'], key="t1")
with col2:
    e2 = st.selectbox("Echipa 2", list(date_echipe.keys()), key="e2")
    t2 = st.multiselect("Titulari E2", date_echipe[e2], format_func=lambda x: x['nume'], key="t2")

if st.button("Simulează Meciul (AI Mode)"):
    if len(t1) < 11 or len(t2) < 11:
        st.warning("Selectează 11 titulari pentru ambele echipe!")
    else:
        # 1. Calculăm puterea ofensivă (Valoare * Formă)
        def calculeaza_putere(titulari):
            # Sumăm (valoare * formă) pentru toți jucătorii
            return sum([j['valoare'] * j['forma'] for j in titulari])

        p1 = calculeaza_putere(t1)
        p2 = calculeaza_putere(t2)
        
        # 2. Calculăm media de goluri (lambda)
        # Scalăm puterea la o medie de goluri plauzibilă în fotbal (ex: între 0.5 și 2.5)
        lambda1 = (p1 / 150) + 0.5 
        lambda2 = (p2 / 150) + 0.5
        
        # 3. Generăm goluri folosind Distribuția Poisson (AI Core)
        s1 = np.random.poisson(lambda1)
        s2 = np.random.poisson(lambda2)
        
        # Plafonare realistă
        s1, s2 = min(s1, 5), min(s2, 5)
        
        # Rezultat
        st.subheader(f"Rezultat Final: {e1} {s1} - {s2} {e2}")
        
        # Detalii AI
        with st.expander("Vezi detaliile analizei AI"):
            st.write(f"Putere ofensivă {e1}: {p1:.2f}")
            st.write(f"Putere ofensivă {e2}: {p2:.2f}")
            st.write(f"Probabilitate medie goluri (Poisson): {lambda1:.2f} vs {lambda2:.2f}")

        # Marcatori (minut aleatoriu)
        if s1 > 0 or s2 > 0:
            st.write("---")
            st.subheader("⚽ Marcatori:")
            for _ in range(s1):
                st.write(f"min. {np.random.randint(1, 90)}' - {e1}: {np.random.choice(t1)['nume']}")
            for _ in range(s2):
                st.write(f"min. {np.random.randint(1, 90)}' - {e2}: {np.random.choice(t2)['nume']}")
        
        st.balloons()
