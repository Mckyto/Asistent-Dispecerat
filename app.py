import streamlit as st
import os
import pandas as pd
import json
from datetime import datetime
from zoneinfo import ZoneInfo

# --- CONFIGURARE ---
FILE_NAME = 'contacte.txt'
DATA_DIR = "rapoarte_zilnice"
STATE_FILE = "sesiune_persistenta.json"
OPERATOR_NUME = "Operator"
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
if not os.path.exists(FILE_NAME): open(FILE_NAME, "w").close()

# --- FUNCȚII PERSISTENȚĂ SESIUNE ---
def salveaza_sesiune(start, actual, lista):
    with open(STATE_FILE, "w") as f:
        json.dump({"start": start, "actual": actual, "lista": lista}, f)

def incarca_sesiune():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f: 
                data = json.load(f)
                return {"start": data.get("start", 0), "actual": data.get("actual", 0), "lista": data.get("lista", [])}
        except: pass
    return {"start": 0, "actual": 0, "lista": []}

# --- FUNCȚII LIVRATORI ---
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

# --- GESTIONARE STATE ---
if 's_data' not in st.session_state:
    st.session_state['s_data'] = incarca_sesiune()

s = st.session_state['s_data']

# --- TAB-URI ---
tab_livr, tab_disp = st.tabs(["🛵 Gestionare Livratori", "⚙️ Dispecerat & Target"])

with tab_livr:
    with st.expander("➕ Adaugă livrator nou"):
        n_n = st.text_input("Nume livrator:")
        if st.button("Salvează livrator"):
            if n_n.strip():
                salveaza_livrator_nou(n_n.strip())
                st.success(f"Livratorul {n_n} a fost adăugat!")
                st.rerun()
            else:
                st.warning("Introdu un nume valid.")
                
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
    col_st, col_ac = st.columns(2)
    start = col_st.number_input("Start:", value=s['start'], step=1)
    actual = col_ac.number_input("Act:", value=s['actual'], step=1)
    
    if start != s['start'] or actual != s['actual']:
        s['start'] = start
        s['actual'] = actual
        salveaza_sesiune(s['start'], s['actual'], s['lista'])
    
    st.info(f"✅ {actual - start} comenzi în total.")
    
    c1, c2 = st.columns([0.4, 0.6])
    with c1:
        with st.expander("🧮 Calculator Discount", expanded=True):
            p = st.number_input("Total (preț):", format="%.2f", key="calc_pret")
            s_val = st.number_input("Încasat:", format="%.2f", key="calc_incasat")
            if st.button("Calculează Discount"):
                diferenta = p - s_val
                st.success(f"Diferență: {diferenta:.2f} lei")

        if st.button("💾 Salvează și Închide Tura"):
            t_t = sum(float(str(i['val']).replace(' lei', '')) for i in s['lista'])
            ora_ro = datetime.now(ZoneInfo("Europe/Bucharest")).strftime('%d_%m_%Y_%H%M%S')
            with open(f"{DATA_DIR}/raport_{OPERATOR_NUME}_{ora_ro}.txt", "w") as f:
                f.write(f"{OPERATOR_NUME}|{actual - start}|{t_t}")
            st.success("Salvat!")
            salveaza_sesiune(0, 0, [])
            st.session_state['s_data'] = incarca_sesiune()
            st.rerun()

        with st.expander("📝 Generează Raport Rapid", expanded=True):
            if st.button("Salvează Raportul cu 859 comenzi și 303.70 lei"):
                ora_ro = datetime.now(ZoneInfo("Europe/Bucharest")).strftime('%d_%m_%Y_%H%M%S')
                with open(f"{DATA_DIR}/raport_{OPERATOR_NUME}_{ora_ro}.txt", "w") as f:
                    f.write(f"{OPERATOR_NUME}|859|303.70")
                st.success("Raportul a fost generat și adăugat în centralizator!")
                st.rerun()

    with c2:
        with st.expander("🎯 Target (Produse cu oră)", expanded=True):
            for produs, val in PRODUSE_BONUS.items():
                cols = st.columns([0.6, 0.2, 0.2])
                cols[0].markdown(f"**{produs}**")
                if cols[1].button("➖", key=f"sub_{produs}"):
                    for i in reversed(range(len(s['lista']))):
                        if s['lista'][i]['nume'] == produs:
                            del s['lista'][i]; break
                    salveaza_sesiune(s['start'], s['actual'], s['lista'])
                    st.rerun()
                if cols[2].button("➕", key=f"add_{produs}"):
                    ora = datetime.now(ZoneInfo("Europe/Bucharest")).strftime("%H:%M")
                    s['lista'].append({"nume": produs, "val": float(val), "ora": ora})
                    salveaza_sesiune(s['start'], s['actual'], s['lista'])
                    st.rerun()
            
            if s['lista']:
                st.divider()
                st.write("📋 **Istoric adăugări:**")
                df = pd.DataFrame(s['lista'])
                cols_to_use = ['ora', 'nume', 'val']
                if all(col in df.columns for col in cols_to_use):
                    df_viz = df.copy()
                    df_viz['val'] = df_viz['val'].apply(lambda x: f"{float(x):.2f} lei")
                    st.table(df_viz[cols_to_use])
                st.write(f"### Total: {sum(float(i['val']) for i in s['lista']):.2f} lei")
                if st.button("RESET TARGET"): 
                    salveaza_sesiune(s['start'], s['actual'], [])
                    s['lista'] = []
                    st.rerun()

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
                    col_a.write(f"📄 **{data_afis}** | {com} com | {float(tgt):.2f} lei")
                    if col_b.button("❌", key=f"del_{f_n}"): os.remove(f"{DATA_DIR}/{f_n}"); st.rerun()
                    total_com += int(com); total_tgt += float(tgt)
                except: continue
        st.metric("Total Comenzi", total_com)
        st.metric("Total Target", f"{total_tgt:.2f} lei")
