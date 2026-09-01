import streamlit as st
import pandas as pd
import requests

# --- CONFIGURARE GENERALĂ ---
st.set_page_config(page_title="Presto & Livratori Hub", page_icon="🍕", layout="wide")
st.title("🍕 Panou Central: Presto & Livratori")

# Link-ul tău de Google Apps Script (Web App)
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxIfS3cIqIy3RwCGIGONNyEyb1PdBSFYGGnpU5f6Rn6KRFsXyLYSKJ_OGooLnQ46JfQZw/exec"

# --- DATE INITIALE ADMIN ---
PRODUSE_INITIALE = [
    ("Baclava", 1.0), ("Tiramisu", 1.0), ("Cheesecake", 1.0), ("Kataif", 1.0),
    ("Placinta cu iaurt/cu mere", 1.0), ("Salam de biscuiti", 1.0), ("Gogosi", 1.0),
    ("Bucket gogosi", 1.0), ("Inghetata", 1.0), ("Limonada", 1.0), ("Hamburger pui", 0.5),
    ("Painica mare", 0.2), ("Paste Quattro Formaggi", 0.5), ("Pizza Napoletta", 1.0),
    ("Painica napolettana", 1.0), ("Pita Gyros", 0.5), ("Bere Porst", 1.0),
    ("Shaorma cu pui crispy", 0.5), ("Salata de pui crispy", 0.5), ("Mozzarella", 0.3),
    ("Grana padano", 0.3), ("Pui ZAO", 1.0),
    ("Mix de fructe prajit/in caramel", 1.0), ("Pui sichuan", 1.0), ("Wings bucket", 2.0),
    ("Apa BAX", 2.0), ("Lapte prajit", 1.0), ("Vita tibetana", 1.0)
]

# --- INIȚIALIZARE SESSION STATE ---
if 'start' not in st.session_state:
    st.session_state['start'] = 0
if 'actual' not in st.session_state:
    st.session_state['actual'] = 0
if 'target' not in st.session_state:
    st.session_state['target'] = 0.0

if 'produse_custom' not in st.session_state:
    st.session_state['produse_custom'] = {nume: val for nume, val in PRODUSE_INITIALE}

# Google Sheets Config Livratori (Export CSV pentru citire rapidă)
SHEET_ID = "1HW_N9cu_6TkQ0Sv3DNIl0ZNVdslFmtXGj-sOCjZQS_Q"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=5)
def incarca_date_livratori():
    try:
        df = pd.read_csv(SHEET_URL)
        df = df.dropna(how='all')
        return df
    except Exception as e:
        st.error(f"Eroare la citirea datelor: {e}")
        return pd.DataFrame()

if "livratori_modificati" not in st.session_state:
    df_google = incarca_date_livratori()
    st.session_state["livratori_modificati"] = df_google.copy()

# --- CREARE TABURI ---
tab_livratori, tab_disp, tab_admin = st.tabs(["🛵 Gestionare Livratori", "⚙️ Dispecerat", "📦 Admin Produse"])

# ==========================================
# 1. TAB LIVRATORI
# ==========================================
with tab_livratori:
    st.header("🛵 Gestionare Livratori")

    with st.expander("➕ Adaugă livrator nou"):
        with st.form("form_add", clear_on_submit=True):
            c1, c2 = st.columns(2)
            nume_nou = c1.text_input("Nume:")
            tel_nou = c2.text_input("Telefon:")
            
            if st.form_submit_button("Salvează livrator"):
                if nume_nou.strip() and tel_nou.strip():
                    valoare_inserata = f"{nume_nou.strip()} - {tel_nou.strip()}"
                    
                    # Trimite datele direct în Google Drive prin scriptul web
                    try:
                        response = requests.post(GOOGLE_SCRIPT_URL, json={"nume": valoare_inserata})
                        if response.status_code == 200:
                            st.success(f"Livratorul '{nume_nou}' a fost adăugat și în Google Sheet!")
                        else:
                            st.warning("Salvat local, dar a apărut o problemă cu Google Sheet.")
                    except Exception as e:
                        st.error(f"Eroare de conexiune cu Google Sheets: {e}")

                    cols = list(st.session_state["livratori_modificati"].columns)
                    col_nume = cols[0] if len(cols) > 0 else "Nume"
                    
                    nou_rand = pd.DataFrame([{col_nume: valoare_inserata}])
                    st.session_state["livratori_modificati"] = pd.concat(
                        [st.session_state["livratori_modificati"], nou_rand], 
                        ignore_index=True
                    )
                    st.rerun()
                else:
                    st.warning("Te rog să completezi ambele câmpuri.")

    cautare = st.text_input("🔎 Căutare livrator (nume sau telefon):")

    if not cautare.strip():
        st.info("💡 Introdu un text în bara de căutare de mai sus pentru a găsi și afișa livratorii.")
    else:
        df_actual = st.session_state["livratori_modificati"]
        
        if not df_actual.empty:
            df_actual = df_actual.fillna("")
            for col in df_actual.columns:
                df_actual[col] = df_actual[col].astype(str).replace("nan", "")
            
            conditie = False
            for col in df_actual.columns:
                conditie = conditie | df_actual[col].str.contains(cautare, case=False, na=False)
                
            rezultate = df_actual[conditie]
            
            st.subheader(f"Rezultate căutare ({len(rezultate)})")

            if rezultate.empty:
                st.warning("Nu a fost găsit niciun livrator.")
            else:
                cols_lista = list(df_actual.columns)
                col_n = cols_lista[0] if len(cols_lista) > 0 else None
                col_t = cols_lista[1] if len(cols_lista) > 1 else None

                for index, row in rezultate.iterrows():
                    with st.container(border=True):
                        c_i, c_t, c_a = st.columns([0.6, 0.3, 0.1])
                        
                        nume_val = row[col_n] if col_n else ""
                        tel_val = row[col_t] if col_t else ""
                        
                        if not tel_val and "-" in nume_val:
                            parti = nume_val.rsplit("-", 1)
                            nume_val = parti[0].strip()
                            tel_val = parti[1].strip()

                        c_i.markdown(f"**{nume_val}**")
                        c_t.markdown(f"📞 {tel_val}" if tel_val else "")
                        
                        if c_a.button("🗑️", key=f"del_livrator_{index}"):
                            st.session_state["livratori_modificati"] = df_actual.drop(index).reset_index(drop=True)
                            st.success("Livrator șters din sesiune!")
                            st.rerun()
        else:
            st.warning("Nu există date disponibile.")

# ==========================================
# 2. TAB DISPECERAT
# ==========================================
with tab_disp:
    st.header("⚙️ Dispecerat Presto")
    
    c1, c2 = st.columns(2)
    st.session_state['start'] = c1.number_input("Start:", value=int(st.session_state['start']), step=1)
    st.session_state['actual'] = c2.number_input("Actual:", value=int(st.session_state['actual']), step=1)

    st.info(f"📦 Comenzi totale: {st.session_state['actual'] - st.session_state['start']}")

    st.subheader("🎯 Adăugare Target")
    with st.form("search_form", clear_on_submit=False):
        query = st.text_input("Scrie produsul și apasă Enter:")
        submit = st.form_submit_button("Caută")

    if submit and query:
        res = [(n, v) for n, v in st.session_state['produse_custom'].items() if query.lower() in n.lower()]
        
        if len(res) == 1:
            st.session_state['target'] += res[0][1]
            st.success(f"Adăugat: {res[0][0]} (+{res[0][1]} lei)")
            st.rerun()
        elif len(res) > 1:
            st.session_state['res_list'] = res
        else:
            st.error("Produs negăsit.")

    if 'res_list' in st.session_state:
        res = st.session_state['res_list']
        optiuni = {f"{p[0]} ({p[1]} lei)": p for p in res}
        sel = st.selectbox("Alege produsul:", options=list(optiuni.keys()))
        if st.button("Confirmă Adăugarea"):
            p_ales = optiuni[sel]
            st.session_state['target'] += p_ales[1]
            del st.session_state['res_list']
            st.rerun()

    st.metric("🎯 Target Acumulat", f"{st.session_state['target']:.2f} lei")
    if st.button("Reset Target"):
        st.session_state['target'] = 0.0
        st.rerun()

# ==========================================
# 3. TAB ADMIN PRODUSE
# ==========================================
with tab_admin:
    st.header("📦 Admin Produse")
    
    st.subheader("➕ Adaugă Produs Nou")
    with st.form("new_prod", clear_on_submit=True):
        n_nume = st.text_input("Nume Produs")
        n_val = st.number_input("Valoare (lei)", step=0.1, min_value=0.0)
        if st.form_submit_button("Salvează"):
            if n_nume.strip():
                nume_curat = n_nume.strip()
                if nume_curat in st.session_state['produse_custom']:
                    st.error("Eroare: Produsul există deja!")
                else:
                    st.session_state['produse_custom'][nume_curat] = n_val
                    st.success("Produs adăugat!")
                    st.rerun()

    st.divider()
    st.subheader("📋 Produse Existente")
    
    produse_sortate = sorted(st.session_state['produse_custom'].items())
    for nume, valoare in produse_sortate:
        col_n, col_v, col_d = st.columns([0.5, 0.3, 0.2])
        col_n.write(nume)
        col_v.write(f"{valoare:.2f} lei")
        if col_d.button("Șterge", key=f"del_prod_{nume}"):
            del st.session_state['produse_custom'][nume]
            st.rerun()
