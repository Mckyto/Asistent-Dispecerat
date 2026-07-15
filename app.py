import streamlit as st
import os
import pandas as pd
from datetime import datetime

# --- CONFIGURARE ---
FILE_NAME = 'contacte.txt'
DATA_DIR = "rapoarte_zilnice"
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
if not os.path.exists(FILE_NAME): open(FILE_NAME, "w").close()

# --- IMPORT ISTORIC ---
istoric_vechi = [("Mihaita", "96", "27.6", "06_07_2026"), ("Mihaita", "87", "26.2", "07_07_2026")]
for nume, com, tgt, data in istoric_vechi:
    cale = f"{DATA_DIR}/raport_{nume}_{data}_000000.txt"
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

# --- SESIUNE NOUĂ ---
if 'lista_produse' not in st.session_state: st.session_state['lista_produse'] = []

operator = st.sidebar.text_input("👤 Operator:", value="Operator1")
start = st.sidebar.number_input("Start:", value=0)
actual = st.sidebar.number_input("Act:", value=0)

with st.sidebar:
    st.info(f"✅ {actual - start} comenzi.")
    
    with st.expander("🧮 Calculator Discount"):
        p = st.number_input("Total (preț):", format="%.2f", key="p_c")
        s = st.number_input("Încasat:", format="%.2f", key="s_c")
        if st.button("Calculează Discount"): st.success(f"Diferență: {p - s:.2f}")

    with st.expander("🎯 Target", expanded=True):
        for produs, val in PRODUSE_BONUS.items():
            with st.container(border=True):
                st.markdown(f"<p style='text-align:center; font-size:14px; font-weight:bold; margin:0;'>{produs}</p>", unsafe_allow_html=True)
                cols = st.columns([1, 1])
                if cols[0].button("➖", key=f"sub_{produs}"):
                    for i in reversed(range(len(st.session_state['lista_produse']))):
                        if st.session_state['lista_produse'][i]['nume'] == produs:
                            del st.session_state['lista_produse'][i]; break
                    st.rerun()
                if cols[1].button("➕", key=f"add_{produs}"):
                    st.session_state['lista_produse'].append({"nume": produs, "val": val}); st.rerun()
        
        if st.session_state['lista_produse']:
            st.divider()
            df = pd.DataFrame(st.session_state['lista_produse'])
            st.table(df.groupby('nume').size().reset_index(name='buc'))
            st.write(f"### Total: {sum(i['val'] for i in st.session_state['lista_produse']):.2f}")
            if st.button("RESET TARGET"): st.session_state['lista_produse'] = []; st.rerun()

    if st.button("💾 Salvează și Închide Tura"):
        d_data = datetime.now().strftime("%d_%m_%Y")
        t_t = sum(i['val'] for i in st.session_state['lista_produse'])
        # Salvăm cu oră în fișier pentru sortare corectă, dar afișăm doar data
        with open(f"{DATA_DIR}/raport_{operator}_{d_data}_{datetime.now().strftime('%H%M%S')}.txt", "w") as f:
            f.write(f"{operator}|{actual - start}|{t_t}")
        st.success("Salvat în istoric!")
        st.session_state['lista_produse'] = []
        st.rerun()

    with st.expander("📊 Centralizator"):
        parola = st.text_input("🔑 Parolă:", type="password")
        if parola == "4676":
            total_com, total_tgt = 0, 0
            fisiere = sorted([f for f in os.listdir(DATA_DIR) if f.startswith("raport_")])
            for f_n in fisiere:
                with open(f"{DATA_DIR}/{f_n}", "r") as f:
                    try:
                        # Extragere dată (DD_MM_YYYY) din nume
                        parti = f_n.replace(".txt", "").split("_")
                        data_afisata = f"{parti[2]}.{parti[3]}.{parti[4]}"
                        
                        op, com, tgt = f.read().split('|')
                        col1, col2 = st.columns([0.8, 0.2])
                        col1.write(f"📄 **{data_afisata}** | {op} | {com} com | {tgt} lei")
                        if col2.button("❌", key=f"del_{f_n}"): os.remove(f"{DATA_DIR}/{f_n}"); st.rerun()
                        total_com += int(com); total_tgt += float(tgt)
                    except: continue
            st.metric("Total Comenzi", total_com)
            st.metric("Total Target", f"{total_tgt:.2f}")
        elif parola: st.error("Parolă incorectă!")

st.subheader("🛵 Gestionare Livratori")
with st.expander("➕ Adaugă livrator nou"):
    n_n = st.text_input("Nume livrator:")
    if st.button("Salvează livrator"):
        l = incarca_livratori(); l.insert(0, n_n); salveaza_livratori(l); st.rerun()

cautare = st.text_input("🔎 Căutare livrator:")
if cautare:
    livr = incarca_livratori()
    gasit = False
    for n in livr:
        if cautare.lower() in n.lower():
            gasit = True
            with st.container(border=True):
                c_i, c_a = st.columns([0.7, 0.3])
                c_i.markdown(f"**{n.upper()}**")
                if c_a.button("Șterge", key=f"d_{n}"):
                    l = incarca_livratori(); l.remove(n); salveaza_livratori(l); st.rerun()
    if not gasit:
        st.warning(f"Livratorul '{cautare}' nu există.")
        if st.button(f"➕ Adaugă-l pe '{cautare}' acum?"):
            l = incarca_livratori(); l.insert(0, cautare); salveaza_livratori(l); st.rerun()
