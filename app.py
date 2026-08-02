import streamlit as st
import os
import pandas as pd
import json
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# --- CONFIGURARE FIȘIERE & SECRETE ---
FILE_NAME = 'contacte.txt'
PONTAJ_FILE = 'pontaj.json'
DATA_DIR = "rapoarte_zilnice"
STATE_FILE = "sesiune_persistenta.json"
PRODUSE_FILE = "produse.json"
OPERATOR_NUME = "Operator"

# Preluare sigură a secretelor de Telegram din Streamlit Secrets
try:
    TELEGRAM_TOKEN = st.secrets["8912058286:AAHbIXJizeKM5PivjSSa4tAuRESNoEvgHmw"]
    TELEGRAM_CHAT_ID = st.secrets["8694128182"]
except:
    TELEGRAM_TOKEN = ""
    TELEGRAM_CHAT_ID = ""

if not os.path.exists(DATA_DIR): 
    os.makedirs(DATA_DIR)
if not os.path.exists(FILE_NAME): 
    open(FILE_NAME, "w").close()
if not os.path.exists(PONTAJ_FILE):
    with open(PONTAJ_FILE, "w") as f:
        json.dump([], f)

# --- FUNCȚIE TRIMITERE TELEGRAM ---
def trimite_pe_telegram(mesaj):
    """Trimite notificări text instant pe Telegram."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mesaj,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=5)
        return response.status_code == 200
    except:
        return False

# --- FUNCȚII PONTAJ ---
def incarca_pontaj():
    if os.path.exists(PONTAJ_FILE):
        try:
            with open(PONTAJ_FILE, "r") as f:
                return json.load(f)
        except: pass
    return []

def salveaza_pontaj(lista_pontaj):
    with open(PONTAJ_FILE, "w") as f:
        json.dump(lista_pontaj, f)

# --- FUNCȚII PERSISTENȚĂ SESIUNE ---
def salveaza_sesiune(start, actual, lista, tura_activa=None):
    with open(STATE_FILE, "w") as f:
        json.dump({"start": start, "actual": actual, "lista": lista, "tura_activa": tura_activa}, f)

def incarca_sesiune():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f: 
                data = json.load(f)
                return {
                    "start": data.get("start", 0), 
                    "actual": data.get("actual", 0), 
                    "lista": data.get("lista", []),
                    "tura_activa": data.get("tura_activa", None)
                }
        except: pass
    return {"start": 0, "actual": 0, "lista": [], "tura_activa": None}

# --- FUNCȚII GESTIONARE PRODUSE ---
def incarca_produse():
    if os.path.exists(PRODUSE_FILE):
        try:
            with open(PRODUSE_FILE, "r") as f:
                produse = json.load(f)
                if "Placinta cu iaurt" in produse:
                    produse["Placinta cu mere"] = produse.pop("Placinta cu iaurt")
                    salveaza_produse(produse)
                return produse
        except: pass
    
    produse_default = {
        "Baclava": 1.0, "Tiramisu": 1.0, "Cheesecake": 1.0, "Kataif": 1.0, 
        "Placinta cu mere": 1.0, "Salam de biscuiti": 1.0, "Gogosi": 1.0, 
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

s = st.session_state['s_data']

# --- VERIFICARE AUTOMATĂ: 12 ORE DE LA CHECK-IN ---
if s.get('tura_activa'):
    try:
        timp_inceput = datetime.strptime(s['tura_activa'], "%Y-%m-%d %H:%M:%S")
        timp_inceput = timp_inceput.replace(tzinfo=ZoneInfo("Europe/Bucharest"))
        timp_acum = datetime.now(ZoneInfo("Europe/Bucharest"))
        
        if timp_acum - timp_inceput >= timedelta(hours=12):
            comenzi_efectuate = s.get('actual', 0) - s.get('start', 0)
            t_t = sum(float(str(i['val']).replace(' lei', '')) for i in s['lista'])
            ora_ro = timp_acum.strftime('%d_%m_%Y_%H%M%S')
            nume_fisier = f"raport_{OPERATOR_NUME}_{ora_ro}.txt"
            continut_raport = f"{OPERATOR_NUME}|{comenzi_efectuate}|{t_t}"
            
            with open(f"{DATA_DIR}/{nume_fisier}", "w") as f:
                f.write(continut_raport)
            
            # Trimite pe Telegram notificare auto 12h
            msg_tg = f"⏰ *Tura automată (12h) s-a încheiat!*\n👤 Operator: {OPERATOR_NUME}\n📦 Comenzi: {comenzi_efectuate}\n🎯 Target: {t_t:.2f} lei"
            trimite_pe_telegram(msg_tg)
            
            timp_sfarsit = timp_inceput + timedelta(hours=12)
            istoric_pontaj = incarca_pontaj()
            istoric_pontaj.append({
                "Operator": OPERATOR_NUME,
                "Data": timp_inceput.strftime("%d.%m.%Y"),
                "Check-in": timp_inceput.strftime("%H:%M"),
                "Check-out": timp_sfarsit.strftime("%H:%M") + " (Auto 12h)",
                "Total Ore": "12.0 ore"
            })
            salveaza_pontaj(istoric_pontaj)
            
            s['start'] = 0
            s['actual'] = 0
            s['lista'] = []
            s['tura_activa'] = None
            salveaza_sesiune(0, 0, [], None)
            
            st.warning("⏰ Au trecut 12 ore! Tura a fost încheiată și trimisă pe Telegram.")
            st.rerun()
    except:
        pass

# --- ORGANIZARE TAB-URI ---
tab_livr, tab_disp, tab_calc, tab_pontaj, tab_centr, tab_admin = st.tabs([
    "🛵 Gestionare Livratori", 
    "⚙️ Dispecerat & Target", 
    "🧮 Calculator Procent",
    "🕐 Pontaj", 
    "📊 Centralizator", 
    "🛠️ Admin Produse"
])

# ==========================================
# 1. TAB LIVRATORI
# ==========================================
with tab_livr:
    st.subheader("🛵 Căutare & Gestionare Livratori")
    cautare = st.text_input("🔎 Introdu numele livratorului pentru căutare:")
    
    livratori_existenti = incarca_livratori()
    
    if cautare.strip():
        termen = cautare.strip().lower()
        gasiti = [n for n in livratori_existenti if termen in n.lower()]
        
        if gasiti:
            st.write("Rezultate găsite:")
            for n in gasiti:
                with st.container(border=True):
                    c_i, c_a = st.columns([0.7, 0.3])
                    c_i.markdown(f"**{n.upper()}**")
                    if c_a.button("Șterge", key=f"d_{n}"):
                        sterge_livrator(n)
                        st.rerun()
        else:
            st.warning(f"Livratorul **'{cautare.strip()}'** nu există în listă.")
            if st.button(f"➕ Adaugă-l pe '{cautare.strip()}' în baza de date"):
                salveaza_livrator_nou(cautare.strip())
                st.success(f"Livratorul {cautare.strip()} a fost adăugat cu succes!")
                st.rerun()
    else:
        st.info("Introdu un nume în căsuța de sus pentru a verifica sau găsi un livrator.")

# ==========================================
# 2. TAB DISPECERAT & TARGET
# ==========================================
with tab_disp:
    col_st, col_ac = st.columns(2)
    start = col_st.number_input("Start:", value=s.get('start', 0), step=1)
    actual = col_ac.number_input("Act:", value=s.get('actual', 0), step=1)
    
    if start != s.get('start', 0) or actual != s.get('actual', 0):
        s['start'] = start
        s['actual'] = actual
        salveaza_sesiune(s['start'], s['actual'], s['lista'], s.get('tura_activa'))
    
    st.info(f"✅ {actual - start} comenzi în total.")
    
    c1, c2 = st.columns([0.4, 0.6])
    with c1:
        with st.expander("🧮 Calculator Discount Vechi", expanded=True):
            p = st.number_input("Total (preț):", format="%.2f", key="calc_pret")
            s_val = st.number_input("Încasat:", format="%.2f", key="calc_incasat")
            if st.button("Calculează Discount"):
                diferenta = p - s_val
                st.success(f"Diferență: {diferenta:.2f} lei")

        if st.button("💾 Salvează și Închide Tura"):
            comenzi_efectuate = actual - start
            t_t = sum(float(str(i['val']).replace(' lei', '')) for i in s['lista'])
            ora_ro = datetime.now(ZoneInfo("Europe/Bucharest")).strftime('%d_%m_%Y_%H%M%S')
            nume_fisier = f"raport_{OPERATOR_NUME}_{ora_ro}.txt"
            continut_raport = f"{OPERATOR_NUME}|{comenzi_efectuate}|{t_t}"
            
            with open(f"{DATA_DIR}/{nume_fisier}", "w") as f:
                f.write(continut_raport)
            
            # Trimite pe Telegram la închiderea turei
            msg_tg = f"✅ *Tură încheiată cu succes!*\n👤 Operator: {OPERATOR_NUME}\n📦 Comenzi: {comenzi_efectuate}\n🎯 Target: {t_t:.2f} lei"
            trimite_pe_telegram(msg_tg)
            
            salveaza_sesiune(0, 0, [], None)
            st.session_state['s_data'] = incarca_sesiune()
            st.success("Tura a fost încheiată, salvată și trimisă pe Telegram!")
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
                    salveaza_sesiune(s['start'], s['actual'], s['lista'], s.get('tura_activa'))
                    st.rerun()
                if cols[2].button("➕", key=f"add_{produs}"):
                    ora = datetime.now(ZoneInfo("Europe/Bucharest")).strftime("%H:%M")
                    s['lista'].append({"nume": produs, "val": float(val), "ora": ora})
                    salveaza_sesiune(s['start'], s['actual'], s['lista'], s.get('tura_activa'))
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
                    s['lista'] = []
                    salveaza_sesiune(s['start'], s['actual'], [], s.get('tura_activa'))
                    st.success("Targetul a fost resetat!")
                    st.rerun()

# ==========================================
# 3. TAB CALCULATOR PROCENT
# ==========================================
with tab_calc:
    st.subheader("🧮 Calculator Avansat de Procentaje")
    
    optiune_calc = st.radio(
        "Ce vrei să calculezi?",
        [
            "1. Cât reprezintă X % dintr-o sumă?",
            "2. Ce procent reprezintă o parte dintr-un total?",
            "3. Aplică o creștere sau reducere procentuală"
        ]
    )
    
    st.divider()
    
    if optiune_calc.startswith("1"):
        st.markdown("#### Cât înseamnă un procent dintr-o sumă?")
        col_c1, col_c2 = st.columns(2)
        val_suma = col_c1.number_input("Valoarea totală (ex: 250):", value=100.0, step=1.0, key="c1_sum")
        val_proc = col_c2.number_input("Procentul % (ex: 15):", value=10.0, step=0.5, key="c1_procent")
        
        rezultat1 = (val_suma * val_proc) / 100
        st.success(f"**Rezultat:** {val_proc}% din {val_suma} este **{rezultat1:.2f}**")

    elif optiune_calc.startswith("2"):
        st.markdown("#### Ce procent reprezintă o parte din total?")
        col_c1, col_c2 = st.columns(2)
        val_parte = col_c1.number_input("Valoarea parțială (ex: 30):", value=20.0, step=1.0, key="c2_parte")
        val_total = col_c2.number_input("Valoarea totală (ex: 150):", value=100.0, step=1.0, key="c2_total")
        
        if val_total > 0:
            rezultat2 = (val_parte / val_total) * 100
            st.success(f"**Rezultat:** {val_parte} reprezintă **{rezultat2:.2f}%** din {val_total}")
        else:
            st.error("Totalul trebuie să fie mai mare decât 0.")

    else:
        st.markdown("#### Creștere sau Reducere Procentuală")
        col_c1, col_c2, col_c3 = st.columns(3)
        val_baza = col_c1.number_input("Suma inițială:", value=100.0, step=1.0, key="c3_baza")
        val_p = col_c2.number_input("Procentul %:", value=10.0, step=0.5, key="c3_p")
        tip_operatie = col_c3.selectbox("Operație:", ["Creștere (+)", "Reducere (-)"])
        
        if tip_operatie.startswith("Creștere"):
            rezultat3 = val_baza + (val_baza * val_p / 100)
            st.success(f"**Rezultat după creștere:** **{rezultat3:.2f}** (Diferență: +{(val_baza * val_p / 100):.2f})")
        else:
            rezultat3 = val_baza - (val_baza * val_p / 100)
            st.success(f"**Rezultat după reducere:** **{rezultat3:.2f}** (Diferență: -{(val_baza * val_p / 100):.2f})")

# ==========================================
# 4. TAB PONTAJ
# ==========================================
with tab_pontaj:
    st.subheader("🕐 Sistem de Pontaj Operator")
    
    col_p1, col_p2 = st.columns(2)
    
    with col_p1:
        if st.button("🟢 Începe Tura (Check-in)", use_container_width=True):
             timp_acum = datetime.now(ZoneInfo("Europe/Bucharest"))
             s['tura_activa'] = timp_acum.strftime("%Y-%m-%d %H:%M:%S")
             salveaza_sesiune(s.get('start', 0), s.get('actual', 0), s.get('lista', []), s['tura_activa'])
             st.success(f"Tura a început la ora {timp_acum.strftime('%H:%M:%S')}!")
             st.rerun()

    with col_p2:
        if st.button("🔴 Încheie Tura (Check-out)", use_container_width=True):
            if s.get('tura_activa'):
                timp_sfarsit = datetime.now(ZoneInfo("Europe/Bucharest"))
                timp_inceput = datetime.strptime(s['tura_activa'], "%Y-%m-%d %H:%M:%S")
                timp_inceput = timp_inceput.replace(tzinfo=ZoneInfo("Europe/Bucharest"))
                
                diferenta = timp_sfarsit - timp_inceput
                ore_lucrate = round(diferenta.total_seconds() / 3600, 2)
                
                istoric_pontaj = incarca_pontaj()
                istoric_pontaj.append({
                    "Operator": OPERATOR_NUME,
                    "Data": timp_inceput.strftime("%d.%m.%Y"),
                    "Check-in": timp_inceput.strftime("%H:%M"),
                    "Check-out": timp_sfarsit.strftime("%H:%M"),
                    "Total Ore": f"{ore_lucrate} ore"
                })
                salveaza_pontaj(istoric_pontaj)
                
                s['tura_activa'] = None
                salveaza_sesiune(s.get('start', 0), s.get('actual', 0), s.get('lista', []), None)
                st.success(f"Tura a fost încheiată! Ai lucrat {ore_lucrate} ore.")
                st.rerun()
            else:
                st.warning("Nu ai nicio tură activă pornită!")

    if s.get('tura_activa'):
        st.info(f"🟢 **Tură activă în curs**, pornită la data și ora: `{s['tura_activa']}` (Se va închide automat după 12 ore)")

    st.divider()
    st.subheader("📋 Istoric Pontaj Ture")
    istoric = incarca_pontaj()
    if istoric:
        df_pontaj = pd.DataFrame(istoric)
        st.table(df_pontaj)
        
        if st.button("🗑️ Șterge tot istoricul de pontaj"):
            salveaza_pontaj([])
            st.success("Istoricul a fost șters!")
            st.rerun()
    else:
        st.info("Nu există înregistrări în pontaj.")

# ==========================================
# 5. TAB CENTRALIZATOR & STATISTICI PRODUSE
# ==========================================
with tab_centr:
    st.subheader("📊 Analiză, Istoric Ture & Pondere Produse")
    
    if s['lista']:
        st.markdown("### 📈 Ponderea produselor în targetul turei curente")
        df_curent = pd.DataFrame(s['lista'])
        
        df_stats = df_curent.groupby('nume').agg(
            Bucati=('val', 'count'),
            ValoareTotala=('val', 'sum')
        ).reset_index()
        
        total_valoare_tura = df_stats['ValoareTotala'].sum()
        df_stats['Procent (%)'] = (df_stats['ValoareTotala'] / total_valoare_tura * 100).round(2)
        df_stats['ValoareTotala'] = df_stats['ValoareTotala'].apply(lambda x: f"{x:.2f} lei")
        df_stats['Procent (%)'] = df_stats['Procent (%)'].apply(lambda x: f"{x}%")
        
        df_stats.columns = ["Produs", "Bucăți", "Valoare (lei)", "Procent din Target"]
        st.dataframe(df_stats, use_container_width=True)
        st.divider()

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
            label="📥 Descarcă Centralizator (CSV) pe dispozitiv",
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
                                
                            st.session_state[f"is_editing_{rand['Fișier']}"] = False
                            st.success("Modificat cu succes!")
                            st.rerun()
                            
                        if col_anuleaza.form_submit_button("Anulează"):
                            st.session_state[f"is_editing_{rand['Fișier']}"] = False
                            st.rerun()
    else:
        st.info("Nu există rapoarte salvate încă. Finalizează o tură pentru a vizualiza centralizatorul.")

# ==========================================
# 6. TAB ADMINISTRARE PRODUSE
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
