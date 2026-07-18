import streamlit as st
import os
import pandas as pd
import json
from datetime import datetime

# --- CONFIGURARE ---
FILE_NAME = 'contacte.txt'
DATA_DIR = "rapoarte_zilnice"
STATE_FILE = "sesiune_persistenta.json"
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
if not os.path.exists(FILE_NAME): open(FILE_NAME, "w").close()

# --- FUNCȚII PERSISTENȚĂ ---
def salveaza_sesiune(op, start, actual, lista):
    with open(STATE_FILE, "w") as f:
        json.dump({"op": op, "start": start, "actual": actual, "lista": lista}, f)

def incarca_sesiune():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f: return json.load(f)
        except: pass
    return {"op": "Operator1", "start": 0, "actual": 0, "lista": []}

# --- IMPORT ISTORIC ---
istoric_preluat = [
    ("Mihaita", "96", "27.6", "06.07.2026"), ("Mihaita", "87", "26.2", "07.07.2026"),
    ("Mihaita", "98", "42.4", "09.07.2026"), ("Mihaita", "100", "26.3", "10.07.2026"),
    ("Mihaita", "90", "47.0", "12.07.2026"), ("Mihaita", "85", "34.1", "13.07.2026"),
    ("Mihaita", "112", "26.8", "15.07.2026"), ("Mihaita", "95", "35.6", "16.07.2026")
]
for nume, com, tgt, data in istoric_preluat:
    d_obj = datetime.strptime(data, "%d.%m.%Y")
    ts = d_obj.strftime("%Y%m%d") + "000000"
    cale = f"{DATA_DIR}/raport_{nume}_{data.replace('.', '_')}_{ts}.txt"
    if not os.path.exists(cale):
        with open(cale, "w") as f: f.write(f"{nume}|{com}|{tgt}")

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

s = incarca_sesiune()
tab1, tab2 = st.tabs(["⚙️ Dispecerat & Target", "🛵 Gestionare Livratori"])

with tab1:
    col_op, col_st, col_ac = st.columns(3)
    operator = col_op.text_input("👤 Operator:", value=s['op'])
    start = col_st.number_input("Start:", value=s['start'])
    actual = col_ac.number_input("Act:", value=s['actual'])
    
    if operator != s['op'] or start != s['start'] or actual != s['actual']:
        salveaza_sesiune(operator, start, actual, s['lista'])
    
    st.info(f"✅ {actual - start} comenzi în total.")
    
    c1, c2 = st.columns([0.4, 0.6])
    with c1:
        if st.button("💾 Salvează și Închide Tura"):
            t_t = sum(float(str(i['val']).replace(' lei', '')) for i in s['lista'])
            with open(f"{DATA_DIR}/raport_{operator}_{datetime.now().strftime('%d_%m_%Y_%H%M%S')}.txt", "w") as f:
                f.write(f"{operator}|{actual - start}|{t_t}")
            st.success("Salvat!")
            salveaza_sesiune("Operator1", 0, 0, [])
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
                    salveaza_sesiune(operator, start, actual, s['lista']); st.rerun()
                if cols[2].button("➕", key=f"add_{produs}"):
                    ora = datetime.now().strftime("%H:%M")
                    s['lista'].append({"nume": produs, "val": float(val), "ora": ora})
                    salveaza_sesiune(operator, start, actual, s['lista']); st.rerun()
            
            if s['lista']:
                st.divider()
                df = pd.DataFrame(s['lista'])
                # Afișăm valoarea formatată frumos în tabel
                df_viz = df.copy()
                df_viz['val'] = df_viz['val'].apply(lambda x: f"{float(x):.2f} lei")
                st.table(df_viz[['ora', 'nume', 'val']])
                st.write(f"### Total: {sum(float(i['val']) for i in s['lista']):.2f} lei")
                if st.button("RESET TARGET"): salveaza_sesiune(operator, start, actual, []); st.rerun()

    with st.expander("📊 Centralizator Ture"):
        parola = st.text_input("🔑 Parolă:", type="password")
        if parola == "4676":
            total_com, total_tgt = 0, 0
            for f_n in sorted(os.listdir(DATA_DIR)):
                if not f_n.startswith("raport_"): continue
                with open(f"{DATA_DIR}/{f_n}", "r") as f:
                    try:
                        op, com, tgt = f.read().split('|')
                        data_afis = f_n.split('_')[2] + "." + f_n.split('_')[3] + "." + f_n.split('_')[4]
                        col_a, col_b = st.columns([0.8, 0.2])
                        col_a.write(f"📄 **{data_afisansat := data_afis}** | {op} | {com} com | {float(tgt):.2f} lei")
                        if col_b.button("❌", key=f"del_{f_n}"): os.remove(f"{DATA_DIR}/{f_n}"); st.rerun()
                        total_com += int(com); total_tgt += float(tgt)
                    except: continue
            st.metric("Total Comenzi", total_com)
            st.metric("Total Target", f"{total_tgt:.2f} lei")

with tab2:
    # (Restul codului pentru livratori rămâne la fel)
    pass
