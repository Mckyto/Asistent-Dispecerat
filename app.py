import streamlit as st
import os
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo

# --- CONFIGURARE ---
FILE_NAME = 'contacte.txt'
DATA_DIR = "rapoarte_zilnice"
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
if not os.path.exists(FILE_NAME): open(FILE_NAME, "w").close()

# --- FUNCȚII LOGICE (LIVRATORI) ---
def incarca_livratori():
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r") as f: return [l.strip() for l in f.readlines() if l.strip()]
    return []

def salveaza_livrator_nou(nume):
    with open(FILE_NAME, "a") as f: 
        f.write(nume + "\n")

def sterge_livrator(nume_de_sters):
    lista = incarca_livratori()
    if nume_de_sters in lista:
        lista.remove(nume_de_sters)
        with open(FILE_NAME, "w") as f:
            for nume in lista: f.write(nume + "\n")

# --- DATE PRODUSE ---
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

# --- INTERFAȚĂ ---
st.set_page_config(page_title="Asistent Presto", page_icon="🍕", layout="wide")
st.title("🍕 Asistent Dispecerat Presto")

if 'lista_produse' not in st.session_state: st.session_state['lista_produse'] = []

# --- TAB-URI ---
tab_livr, tab_disp = st.tabs(["🛵 Gestionare Livratori", "⚙️ Dispecerat & Target"])

with tab_livr:
    with st.expander("➕ Adaugă livrator nou"):
        n_n = st.text_input("Nume livrator:")
        if st.button("Salvează livrator"):
            salveaza_livrator_nou(n_n)
            st.rerun()
    cautare = st.text_input("🔎 Căutare livrator:")
    if cautare:
        for n in incarca_livratori():
            if cautare.lower() in n.lower():
                with st.container(border=True):
                    c_i, c_a = st.columns([0.7, 0.3])
                    c_i.markdown(f"**{n.upper()}**")
                    if c_a.button("Șterge", key=f"d_{n}"):
                        sterge_livrator(n)
                        st.rerun()

with tab_disp:
    col_op, col_st, col_ac = st.columns(3)
    operator = col_op.text_input("👤 Operator:", value="Operator1")
    start = col_st.number_input("Start:", value=0)
    actual = col_ac.number_input("Act:", value=0)
    
    st.info(f"✅ {actual - start} comenzi în total.")
    
    c1, c2 = st.columns([0.4, 0.6])
    with c1:
        if st.button("💾 Salvează și Închide Tura"):
            t_t = sum(float(str(i['val']).replace(' lei', '')) for i in st.session_state['lista_produse'])
            ora_ro = datetime.now(ZoneInfo("Europe/Bucharest")).strftime('%d_%m_%Y_%H%M%S')
            with open(f"{DATA_DIR}/raport_{operator}_{ora_ro}.txt", "w") as f:
                f.write(f"{operator}|{actual - start}|{t_t}")
            st.success("Salvat!")
            st.session_state['lista_produse'] = []
            st.rerun()

    with c2:
        with st.expander("🎯 Target (Produse cu oră)", expanded=True):
            for produs, val in PRODUSE_BONUS.items():
                cols = st.columns([0.6, 0.2, 0.2])
                cols[0].markdown(f"**{produs}**")
                if cols[1].button("➖", key=f"sub_{produs}"):
                    for i in reversed(range(len(st.session_state['lista_produse']))):
                        if st.session_state['lista_produse'][i]['nume'] == produs:
                            del st.session_state['lista_produse'][i]; break
                    st.rerun()
                if cols[2].button("➕", key=f"add_{produs}"):
                    ora = datetime.now(ZoneInfo("Europe/Bucharest")).strftime("%H:%M")
                    st.session_state['lista_produse'].append({"nume": produs, "val": float(val), "ora": ora})
                    st.rerun()
            
            if st.session_state['lista_produse']:
                st.divider()
                st.write("📋 **Istoric adăugări:**")
                df = pd.DataFrame(st.session_state['lista_produse'])
                cols_to_use = ['ora', 'nume', 'val']
                if all(col in df.columns for col in cols_to_use):
                    df_viz = df.copy()
                    df_viz['val'] = df_viz['val'].apply(lambda x: f"{float(x):.2f} lei")
                    st.table(df_viz[cols_to_use])
                st.write(f"### Total: {sum(float(i['val']) for i in st.session_state['lista_produse']):.2f} lei")
                if st.button("RESET TARGET"): st.session_state['lista_produse'] = []; st.rerun()

    with st.expander("📊 Centralizator Ture"):
        total_com, total_tgt = 0, 0
        for f_n in sorted(os.listdir(DATA_DIR)):
            if not f_n.startswith("raport_"): continue
            with open(f"{DATA_DIR}/{f_n}", "r") as f:
                try:
                    op, com, tgt = f.read().split('|')
                    parti = f_n.split('_')
                    data_afis = f"{parti[2]}.{parti[3]}.{parti[4]}"
                    col_a, col_b = st.columns([0.8, 0.2])
                    col_a.write(f"📄 **{data_afis}** | {op} | {com} com | {float(tgt):.2f} lei")
                    if col_b.button("❌", key=f"del_{f_n}"): os.remove(f"{DATA_DIR}/{f_n}"); st.rerun()
                    total_com += int(com); total_tgt += float(tgt)
                except: continue
        st.metric("Total Comenzi", total_com)
        st.metric("Total Target", f"{total_tgt:.2f} lei")
