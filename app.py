import streamlit as st
import os
import pandas as pd
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from github import Github

# --- CONFIGURARE FIȘIERE & SECRETE HARDCODATE ---
FILE_NAME = 'contacte.txt'
DATA_DIR = "rapoarte_zilnice"
STATE_FILE = "sesiune_persistenta.json"
PRODUSE_FILE = "produse.json"
OPERATOR_NUME = "Operator"
PAROLA_DISPECERAT = "presto2026"

# Datele tale de GitHub integrate direct
GITHUB_TOKEN_VAL = "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"
GITHUB_REPO_VAL = "Mckyto/predict"

if not os.path.exists(DATA_DIR): 
    os.makedirs(DATA_DIR)
if not os.path.exists(FILE_NAME): 
    open(FILE_NAME, "w").close()

# --- FUNCȚIE SALVARE AUTOMATĂ PE GITHUB ---
def salveaza_pe_github(nume_fisier, continut_text):
    try:
        g = Github(GITHUB_TOKEN_VAL)
        repo = g.get_repo(GITHUB_REPO_VAL)
        path = f"{DATA_DIR}/{nume_fisier}"
        message = f"Adaugă raport automat {nume_fisier}"
        
        try:
            file = repo.get_contents(path)
            repo.update_file(path, message, continut_text, file.sha)
        except:
            repo.create_file(path, message, continut_text)
        return True
    except Exception as e:
        st.warning(f"Salvarea pe GitHub a eșuat, s-a salvat doar local: {e}")
    return False

# --- FUNCȚII PERSISTENȚĂ SESIUNE ---
def salveaza_sesiune(start, actual, lista):
    with open(STATE_FILE, "w") as f:
        json.dump({"start": start, "actual": actual, "lista": lista}, f)

def incarca_sesiune():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f: 
                data = json.load(f)
                return {
                    "start": data.get("start", 0), 
                    "actual": data.get("actual", 0), 
                    "lista": data.get("lista", [])
                }
        except: pass
    return {"start": 0, "actual": 0, "lista": []}

# --- FUNCȚII GESTIONARE PRODUSE ---
def incarca_produse():
    if os.path.exists(PRODUSE_FILE):
        try:
            with open(PRODUSE_FILE, "r") as f:
                return json.load(f)
        except: pass
    
    produse_default = {
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
    with open(PRODUSE_FILE, "w") as f:
        json.dump(produse_default, f)
    return produse_default

def salveaza_produse(produse_dict):
    with open(PRODUSE_FILE, "w") as f:
        json.dump(produse_dict, f)

# --- FUNCȚII LIVRATORI ---
def incarca_livratori():
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r") as f: 
            return [l.strip() for l in f.readlines() if l.strip()]
    return []

def salveaza_livrator_nou(nume):
    with open(FILE_NAME, "a") as f: 
        f.write(nume + "\n")

def sterge_livrator(nume_de_sters):
    lista = incarca_livratori()
    if nume_de_sters in lista:
        lista.remove(nume_de_sters)
        with open(FILE_NAME, "w") as f:
            for nume in lista: 
                f.write(nume + "\n")

# --- INTERFAȚĂ PRINCIPALĂ ---
st.set_page_config(page_title="Asistent Presto", page_icon="🍕", layout="wide")
st.title("🍕 Asistent Dispecerat Presto")

# --- INITIALIZARE SESSION STATE ---
if 's_data' not in st.session_state:
    st.session_state['s_data'] = incarca_sesiune()
if 'produse_bonus' not in st.session_state:
    st.session_state['produse_bonus'] = incarca_produse()
if 'autentificat_disp' not in st.session_state:
    st.session_state['autentificat_disp'] = False

s = st.session_state['s_data']

# --- ORGANIZARE TAB-URI ---
tab_livr, tab_disp, tab_centr, tab_admin = st.tabs([
    "🛵 Gestionare Livratori", 
    "⚙️ Dispecerat & Target", 
    "📊 Centralizator", 
    "🛠️ Admin Produse"
])

# ==========================================
# 1. TAB LIVRATORI
# ==========================================
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

# ==========================================
# 2. TAB DISPECERAT & TARGET (Protejat cu parolă)
# ==========================================
with tab_disp:
    if not st.session_state['autentificat_disp']:
        st.subheader("🔐 Acces Protejat")
        parola_intrata = st.text_input("Introdu parola pentru Dispecerat & Target:", type="password")
        if st.button("Autentificare"):
            if parola_intrata == PAROLA_DISPECERAT:
                st.session_state['autentificat_disp'] = True
                st.success("Acces permis!")
                st.rerun()
            else:
                st.error("Parolă incorectă!")
    else:
        col_deconectare, col_status = st.columns([0.8, 0.2])
        col_status.caption("⚡ Auto-Save activat")
        if col_deconectare.button("🔒 Deconectare"):
            st.session_state['autentificat_disp'] = False
            st.rerun()
            
        st.divider()
        col_st, col_ac = st.columns(2)
        start = col_st.number_input("Start:", value=s.get('start', 0), step=1)
        actual = col_ac.number_input("Act:", value=s.get('actual', 0), step=1)
        
        if start != s.get('start', 0) or actual != s.get('actual', 0):
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
                nume_fisier = f"raport_{OPERATOR_NUME}_{ora_ro}.txt"
                continut_raport = f"{OPERATOR_NUME}|{actual - start}|{t_t}"
                
                with open(f"{DATA_DIR}/{nume_fisier}", "w") as f:
                    f.write(continut_raport)
                
                salveaza_pe_github(nume_fisier, continut_raport)
                
                st.success("Salvat cu succes local și pe GitHub!")
                salveaza_sesiune(0, 0, [])
                st.session_state['s_data'] = incarca_sesiune()
                st.rerun()

        with c2:
            with st.expander("🎯 Target (Toate Produsele Active)", expanded=True):
                for produs, val in st.session_state['produse_bonus'].items():
                    cols = st.columns([0.6, 0.2, 0.2])
                    cols[0].markdown(f"**{produs}** `({val} lei)`")
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

# ==========================================
# 3. TAB CENTRALIZATOR & EDITARE RAPOARTE
# ==========================================
with tab_centr:
    st.subheader("📊 Analiză și Istoric Ture")
    total_com, total_tgt = 0, 0
    date_rapoarte = []
    
    for f_n in sorted(os.listdir(DATA_DIR)):
        if not f_n.startswith("raport_"): continue
        with open(f"{DATA_DIR}/{f_n}", "r") as f:
            try:
                op, com, tgt = f.read().split('|')
                parti = f_n.split('_')
                zi, luna, an = parti[2], parti[3], parti[4]
                data_afis = f"{zi}.{luna}.{an}" 
                
                date_rapoarte.append({
                    "Fișier": f_n, "Data": data_afis, 
                    "Zi": zi, "Luna": luna, "An": an,
                    "Comenzi": int(com), "Target": float(tgt)
                })
                total_com += int(com)
                total_tgt += float(tgt)
            except: continue

    col_m1, col_m2 = st.columns(2)
    col_m1.metric("Total Comenzi", total_com)
    col_m2.metric("Total Target", f"{total_tgt:.2f} lei")
    
    if date_rapoarte:
        st.divider()
        df_rapoarte = pd.DataFrame(date_rapoarte)
        
        df_export = df_rapoarte[['Data', 'Comenzi', 'Target']].copy()
        csv_data = df_export.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            label="📥 Descarcă Centralizator (CSV)",
            data=csv_data,
            file_name="raport_comenzi_presto.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        st.divider()
        df_grafic = df_rapoarte.groupby("Data")["Comenzi"].sum().reset_index()
        st.write("📈 **Evoluție Comenzi Zilnice**")
        st.bar_chart(df_grafic, x="Data", y="Comenzi", color="#ff4b4b")
        
        st.divider()
        st.write("📋 **Istoric Detaliat Ture (Editează Data / Comenzi / Target sau Șterge)**")
        
        for rand in date_rapoarte:
            with st.container(border=True):
                c_info, c_ed, c_del = st.columns([0.6, 0.2, 0.2])
                c_info.write(f"📄 **{rand['Data']}** | {rand['Comenzi']} com | {rand['Target']:.2f} lei")
                
                editeaza_apasat = c_ed.button("✏️ Editează", key=f"edit_btn_{rand['Fișier']}")
                
                if c_del.button("❌ Șterge", key=f"del_{rand['Fișier']}"): 
                    os.remove(f"{DATA_DIR}/{rand['Fișier']}")
                    st.rerun()
                
                if editeaza_apasat:
                    st.session_state[f"is_editing_{rand['Fișier']}"] = True
                
                if st.session_state.get(f"is_editing_{rand['Fișier']}", False):
                    with st.form(key=f"form_edit_{rand['Fișier']}"):
                        st.write(f"Modificare raport: {rand['Fișier']}")
                        
                        data_curenta_obj = datetime.strptime(rand['Data'], "%d.%m.%Y")
                        noua_data = st.date_input("Data raportului:", value=data_curenta_obj)
                        
                        nou_com = st.number_input("Comenzi:", value=rand['Comenzi'], step=1)
                        nou_tgt = st.number_input("Target (lei):", value=rand['Target'], format="%.2f", step=0.1)
                        
                        col_salveaza, col_anuleaza = st.columns(2)
                        if col_salveaza.form_submit_button("Salvează Modificările"):
                            n_zi = noua_data.strftime("%d")
                            n_luna = noua_data.strftime("%m")
                            n_an = noua_data.strftime("%Y")
                            
                            parti_vechi = rand['Fișier'].split('_')
                            ora_veche = parti_vechi[5] if len(parti_vechi) > 5 else "000000.txt"
                            
                            nume_nou_fisier = f"raport_{OPERATOR_NUME}_{n_zi}_{n_luna}_{n_an}_{ora_veche}"
                            
                            if rand['Fișier'] != nume_nou_fisier:
                                if os.path.exists(f"{DATA_DIR}/{rand['Fișier']}"):
                                    os.remove(f"{DATA_DIR}/{rand['Fișier']}")
                            
                            continut_nou = f"{OPERATOR_NUME}|{nou_com}|{nou_tgt}"
                            with open(f"{DATA_DIR}/{nume_nou_fisier}", "w") as f_out:
                                f_out.write(continut_nou)
                                
                            salveaza_pe_github(nume_nou_fisier, continut_nou)
                                
                            st.session_state[f"is_editing_{rand['Fișier']}"] = False
                            st.success("Modificat cu succes!")
                            st.rerun()
                            
                        if col_anuleaza.form_submit_button("Anulează"):
                            st.session_state[f"is_editing_{rand['Fișier']}"] = False
                            st.rerun()
    else:
        st.info("Nu există rapoarte salvate încă. Finalizează o tură pentru a vizualiza centralizatorul.")

# ==========================================
# 4. TAB ADMINISTRARE PRODUSE
# ==========================================
with tab_admin:
    st.subheader("➕ Adaugă sau Actualizează Produs")
    
    with st.container(border=True):
        c_nume, c_val, c_btn = st.columns([0.5, 0.25, 0.25])
        nume_p = c_nume.text_input("Nume Produs:", key="input_nume_p")
        valoare_p = c_val.number_input("Valoare (lei):", min_value=0.0, step=0.1, format="%.2f")
        
        c_btn.write("") 
        c_btn.write("")
        if c_btn.button("Salvează", use_container_width=True):
            if nume_p.strip():
                st.session_state['produse_bonus'][nume_p.strip()] = valoare_p
                salveaza_produse(st.session_state['produse_bonus'])
                st.success(f"Salvat: {nume_p}")
                st.rerun()
            else:
                st.warning("Introdu un nume valid.")

    st.subheader("📋 Catalog Produse Active")
    cautare_p = st.text_input("🔎 Caută în meniu...")
    
    for prod, val in list(st.session_state['produse_bonus'].items()):
        if cautare_p.lower() in prod.lower():
            with st.container(border=True):
                col_info, col_del = st.columns([0.8, 0.2])
                col_info.markdown(f"**{prod}** — {val} lei")
                if col_del.button("Șterge", key=f"del_p_{prod}", type="secondary", use_container_width=True):
                    del st.session_state['produse_bonus'][prod]
                    salveaza_produse(st.session_state['produse_bonus'])
                    st.rerun()
