import streamlit as st
import os
import pandas as pd
from datetime import datetime

# --- CONFIGURARE ---
FILE_NAME = 'contacte.txt'
DATA_DIR = "rapoarte_zilnice"
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
if not os.path.exists(FILE_NAME): open(FILE_NAME, "w").close()

# --- IMPORT ISTORIC (Datele tale) ---
istoric_preluat = [
    ("Mihaita", "96", "27.6", "06.07.2026"), ("Mihaita", "87", "26.2", "07.07.2026"),
    ("Mihaita", "98", "42.4", "09.07.2026"), ("Mihaita", "100", "26.3", "10.07.2026"),
    ("Mihaita", "90", "47.0", "12.07.2026"), ("Mihaita", "85", "34.1", "13.07.2026"),
    ("Mihaita", "112", "26.8", "15.07.2026"), ("Mihaita", "95", "35.6", "16.07.2026")
]

for nume, com, tgt, data in istoric_preluat:
    # Generăm un timestamp fictiv pentru sortare (folosind data)
    d_obj = datetime.strptime(data, "%d.%m.%Y")
    ts = d_obj.strftime("%Y%m%d") + "000000"
    cale = f"{DATA_DIR}/raport_{nume}_{data.replace('.', '_')}_{ts}.txt"
    if not os.path.exists(cale):
        with open(cale, "w") as f: f.write(f"{nume}|{com}|{tgt}")

# --- FUNCȚII ---
def incarca_livratori():
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r") as f: return [l.strip() for l in f.readlines() if l.strip()]
    return []

def salveaza_livratori(lista):
    with open(FILE_NAME, "w") as f:
        for nume in lista: f.write(nume + "\n")

PRODUSE_BONUS = {
    "Baclava": 1.0, "Tiramisu": 1.0, "Cheesecake": 1.0, "Kataif": 1.0, 
    "Placinta cu iaurt": 1.0, "Salam de biscuiti": 1.0, "Gogosi": 1.0, 
    "Bucket gogosi": 1.0, "Inghetata": 1.0, "Limonada": 1.0, 
    "Hamburger pui": 0.2, "Painica mare": 0.5, "Paste Quattro Formaggi": 1.0, 
    "Pizza Napoletta": 1.0, "Painica napolettana": 0.5, "Pita Gyros": 1.0, 
    "Bere Porst": 0.5, "Shaorma cu pui crispy": 0.5, "Salata de pui crispy": 0.3, 
    "Mozzarella": 0.3, "Grana padano": 1.0, "Vita tibetana": 1.0, 
    "Pui ZAO": 1.0, "Mix de fructe prajit/in caramel": 1.0, "Lapte prajit": 1.0, 
    "Pui sichuan": 1.0, "Wings bucket": 2.0, "Apa BAX": 2.0
}

st.set_page_config(page_title="Asistent Presto", page_icon="🍕", layout="wide")
st.title("🍕 Asistent Dispecerat Presto")

tab1, tab2 = st.tabs(["⚙️ Dispecerat & Target", "🛵 Gestionare Livratori"])

with tab1:
    if 'lista_produse' not in st.session_state: st.session_state['lista_produse'] = []
    col_op, col_st, col_ac = st.columns(3)
    operator = col_op.text_input("👤 Operator:", value="Operator1")
    start = col_st.number_input("Start:", value=0)
    actual = col_ac.number_input("Act:", value=0)
    
    st.info(f"✅ {actual - start} comenzi în total.")
    
    c1, c2 = st.columns([0.4, 0.6])
    with c1:
        with st.expander("🧮 Calculator Discount", expanded=True):
            p = st.number_input("Total (preț):", format="%.2f")
            s = st.number_input("Încasat:", format="%.2f")
            if st.button("Calculează Discount"): st.success(f"Diferență: {p - s:.2f}")
        
        if st.button("💾 Salvează și Închide Tura"):
            d_t = datetime.now().strftime("%d_%m_%Y_%H%M%S")
            t_t = sum(i['val'] for i in st.session_state['lista_produse'])
            with open(f"{DATA_DIR}/raport_{operator}_{datetime.now().strftime('%d_%m_%Y')}_{d_t}.txt", "w") as f:
                f.write(f"{operator}|{actual - start}|{t_t}")
            st.success("Salvat în istoric!")
            st.session_state['lista_produse'] = []
            st.rerun()

    with c2:
        with st.expander("🎯 Target (Produse)", expanded=True):
            for produs, val in PRODUSE_BONUS.items():
                cols = st.columns([0.6, 0.2, 0.2])
                cols[0].markdown(f"**{produs}**")
                if cols[1].button("➖", key=f"sub_{produs}"):
                    for i in reversed(range(len(st.session_state['lista_produse']))):
                        if st.session_state['lista_produse'][i]['nume'] == produs:
                            del st.session_state['lista_produse'][i]; break
                    st.rerun()
                if cols[2].button("➕", key=f"add_{produs}"):
                    st.session_state['lista_produse'].append({"nume": produs, "val": val}); st.rerun()
            
            if st.session_state['lista_produse']:
                st.divider()
                df = pd.DataFrame(st.session_state['lista_produse'])
                st.table(df.groupby('nume').size().reset_index(name='buc'))
                st.write(f"### Total: {sum(i['val'] for i in st.session_state['lista_produse']):.2f}")
                if st.button("RESET TARGET"): st.session_state['lista_produse'] = []; st.rerun()

    with st.expander("📊 Centralizator Ture"):
        parola = st.text_input("🔑 Parolă Centralizator:", type="password")
        if parola == "4676":
            fisiere = sorted([f for f in os.listdir(DATA_DIR) if f.startswith("raport_")])
            for f_n in fisiere:
                with open(f"{DATA_DIR}/{f_n}", "r") as f:
                    parti = f_n.replace(".txt", "").split("_")
                    data_afisata = f"{parti[2]}.{parti[3]}.{parti[4]}"
                    op, com, tgt = f.read().split('|')
                    c_r1, c_r2 = st.columns([0.8, 0.2])
                    c_r1.write(f"📄 **{data_afisata}** | {op} | {com} com | {tgt} lei")
                    if c_r2.button("❌", key=f"del_{f_n}"): os.remove(f"{DATA_DIR}/{f_n}"); st.rerun()
        elif parola: st.error("Parolă incorectă!")

with tab2:
    with st.expander("➕ Adaugă livrator nou"):
        n_n = st.text_input("Nume livrator:")
        if st.button("Salvează livrator"):
            l = incarca_livratori(); l.insert(0, n_n); salveaza_livratori(l); st.rerun()
    cautare = st.text_input("🔎 Căutare livrator:")
    if cautare:
        for n in incarca_livratori():
            if cautare.lower() in n.lower():
                with st.container(border=True):
                    c_i, c_a = st.columns([0.7, 0.3])
                    c_i.markdown(f"**{n.upper()}**")
                    if c_a.button("Șterge", key=f"d_{n}"):
                        l = incarca_livratori(); l.remove(n); salveaza_livratori(l); st.rerun()
