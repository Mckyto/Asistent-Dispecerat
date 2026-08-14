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
RAPOARTE_JSON = 'rapoarte_salvate.json'
STATE_FILE = "sesiune_persistenta.json"
PRODUSE_FILE = "produse.json"
OPERATOR_NUME = "Operator"

# Preluare sigură a secretelor de Telegram din Streamlit Secrets
try:
    TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
    TELEGRAM_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
except:
    TELEGRAM_TOKEN = ""
    TELEGRAM_CHAT_ID = ""

# --- CURĂȚARE SIGURĂ FIȘIERE CORUPTE ---
for f_path in [PONTAJ_FILE, RAPOARTE_JSON, STATE_FILE]:
    if os.path.exists(f_path):
        try:
            with open(f_path, "r") as f:
                json.load(f)
        except:
            os.remove(f_path)

if not os.path.exists(FILE_NAME): 
    open(FILE_NAME, "w").close()
if not os.path.exists(PONTAJ_FILE):
    with open(PONTAJ_FILE, "w") as f:
        json.dump([], f)
if not os.path.exists(RAPOARTE_JSON):
    with open(RAPOARTE_JSON, "w") as f:
        json.dump([], f)
if not os.path.exists(PRODUSE_FILE):
    with open(PRODUSE_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=4)

# --- FUNCȚIE TRIMITERE TELEGRAM ---
def trimite_pe_telegram(mesaj):
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

# --- FUNCȚII GESTIONARE RAPOARTE (JSON STABIL) ---
def incarca_rapoarte_json():
    if os.path.exists(RAPOARTE_JSON):
        try:
            with open(RAPOARTE_JSON, "r") as f:
                return json.load(f)
        except: pass
    return []

def salveaza_rapoarte_json(lista_rapoarte):
    with open(RAPOARTE_JSON, "w") as f:
        json.dump(lista_rapoarte, f, indent=4)

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
def salveaza_sesiune(start, actual, target_manual_val, tura_activa=None, target_items=None):
    if target_items is None:
        target_items = st.session_state.get("target_items", {})
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "start": start,
            "actual": actual,
            "target_manual_val": target_manual_val,
            "target_items": target_items,
            "tura_activa": tura_activa
        }, f, ensure_ascii=False)

def incarca_sesiune():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {
                    "start": data.get("start", 0),
                    "actual": data.get("actual", 0),
                    "target_manual_val": data.get("target_manual_val", 0.0),
                    "target_items": data.get("target_items", {}),
                    "tura_activa": data.get("tura_activa", None)
                }
        except Exception:
            pass
    return {
        "start": 0,
        "actual": 0,
        "target_manual_val": 0.0,
        "target_items": {},
        "tura_activa": None
    }

# --- FUNCȚII GESTIONARE PRODUSE ---
def incarca_produse():
    """Încarcă exact produsele existente în Admin din produse.json.
    Nu creează produse implicite și nu modifică lista existentă.
    """
    if os.path.exists(PRODUSE_FILE):
        try:
            with open(PRODUSE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return {}


def salveaza_produse(produse):
    with open(PRODUSE_FILE, "w", encoding="utf-8") as f:
        json.dump(produse, f, ensure_ascii=False, indent=4)


def cauta_produse(termen):
    """Caută numai în produsele existente în Admin."""
    produse = incarca_produse()
    termen = " ".join(str(termen).strip().lower().split())
    if not termen:
        return []

    rezultate = []
    for nume, valoare in produse.items():
        if termen in str(nume).lower():
            try:
                rezultate.append((str(nume), float(valoare)))
            except (TypeError, ValueError):
                continue

    # Potrivirea exactă este întotdeauna prima.
    rezultate.sort(key=lambda x: (x[0].lower() != termen, x[0].lower()))
    return rezultate


def adauga_produs_la_target(nume, valoare):
    """Adaugă o bucată dintr-un produs existent în Admin la target."""
    if "target_items" not in st.session_state:
        st.session_state["target_items"] = {}

    items = st.session_state["target_items"]
    items[nume] = int(items.get(nume, 0)) + 1

    s_local = st.session_state["s_data"]
    s_local["target_manual_val"] = round(
        float(s_local.get("target_manual_val", 0.0)) + float(valoare),
        2,
    )

    salveaza_sesiune(
        s_local["start"],
        s_local["actual"],
        s_local["target_manual_val"],
        s_local.get("tura_activa"),
        items,
    )


def elimina_produs_din_target(nume, valoare):
    items = st.session_state.get("target_items", {})
    cantitate = int(items.get(nume, 0))

    if cantitate <= 0:
        return

    if cantitate == 1:
        items.pop(nume, None)
    else:
        items[nume] = cantitate - 1

    s_local = st.session_state["s_data"]
    s_local["target_manual_val"] = round(
        max(0.0, float(s_local.get("target_manual_val", 0.0)) - float(valoare)),
        2,
    )

    salveaza_sesiune(
        s_local["start"],
        s_local["actual"],
        s_local["target_manual_val"],
        s_local.get("tura_activa"),
        items,
    )


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

# --- MENIU SIDEBAR PENTRU TESTARE BOT ---
st.sidebar.header("🛠️ Setări & Teste")
if st.sidebar.button("🧪 Testează Bot Telegram"):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        st.sidebar.error("Lipsesc TELEGRAM_TOKEN sau TELEGRAM_CHAT_ID din Streamlit Secrets!")
    else:
        rezultat = trimite_pe_telegram("🤖 *Test reușit!* Botul Presto este activ și pregătit să trimită rapoartele.")
        if rezultat:
            st.sidebar.success("Mesajul de test a fost trimis pe Telegram!")
        else:
            st.sidebar.error("Eroare la trimitere. Verifică datele din Secrets.")

# --- INITIALIZARE SESSION STATE ---
if 's_data' not in st.session_state:
    st.session_state['s_data'] = incarca_sesiune()

s = st.session_state['s_data']
if 'target_items' not in st.session_state:
    st.session_state['target_items'] = dict(s.get('target_items', {}))

# --- VERIFICARE AUTOMATĂ: 12 ORE DE LA CHECK-IN ---
if s.get('tura_activa'):
    try:
        timp_inceput = datetime.strptime(s['tura_activa'], "%Y-%m-%d %H:%M:%S")
        timp_inceput = timp_inceput.replace(tzinfo=ZoneInfo("Europe/Bucharest"))
        timp_acum = datetime.now(ZoneInfo("Europe/Bucharest"))
        
        if timp_acum - timp_inceput >= timedelta(hours=12):
            comenzi_efectuate = s.get('actual', 0) - s.get('start', 0)
            t_t = s.get('target_manual_val', 0.0)
            
            rapoarte = incarca_rapoarte_json()
            rapoarte.append({
                "id": datetime.now().strftime("%Y%m%d%H%M%S"),
                "Data": timp_inceput.strftime("%d.%m.%Y"),
                "Comenzi": comenzi_efectuate,
                "Target": t_t
            })
            salveaza_rapoarte_json(rapoarte)
            
            msg_tg = f"⏰ *Tura automată (12h) s-a încheiat!*\n👤 Operator: {OPERATOR_NUME}\n📦 Comenzi totale: {comenzi_efectuate}\n🎯 Target total: {t_t:.2f} lei"
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
            s['target_manual_val'] = 0.0
            s['target_items'] = {}
            st.session_state['target_items'] = {}
            s['tura_activa'] = None
            salveaza_sesiune(0, 0, 0.0, None, {})
            
            st.warning("⏰ Au trecut 12 ore! Tura a fost încheiată și salvată în baza de date.")
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
        salveaza_sesiune(s['start'], s['actual'], s['target_manual_val'], s.get('tura_activa'))
    
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
            t_t = s.get('target_manual_val', 0.0)
            
            rapoarte = incarca_rapoarte_json()
            rapoarte.append({
                "id": datetime.now().strftime("%Y%m%d%H%M%S"),
                "Data": datetime.now(ZoneInfo("Europe/Bucharest")).strftime("%d.%m.%Y"),
                "Comenzi": comenzi_efectuate,
                "Target": t_t
            })
            salveaza_rapoarte_json(rapoarte)
            
            msg_tg = f"✅ *RAPORT TURĂ Încheiată*\n👤 Operator: {OPERATOR_NUME}\n📦 Comenzi totale: *{comenzi_efectuate}*\n🎯 Target total acumulat: *{t_t:.2f} lei*"
            trimite_pe_telegram(msg_tg)
            
            salveaza_sesiune(0, 0, 0.0, None, {})
            st.session_state['target_items'] = {}
            st.session_state['s_data'] = incarca_sesiune()
            st.success("Tura a fost încheiată, salvată în baza de date și raportul a fost trimis pe Telegram!")
            st.rerun()

    with c2:
        with st.expander("🎯 Target — Caută produs și confirmă cu Enter", expanded=True):
            target_total = float(s.get("target_manual_val", 0.0))
            st.metric("Target curent", f"{target_total:.2f} lei")

            st.caption(
                "Caută numai produsele existente în Admin Produse. "
                "Scrie numele și apasă Enter."
            )

            with st.form("target_search_form", clear_on_submit=True):
                cautare_produs = st.text_input(
                    "🔎 Caută produs:",
                    placeholder="Ex.: baclava, tiramisu, pizza...",
                )
                confirmare = st.form_submit_button(
                    "↵ ENTER — Confirmă produsul",
                    type="primary",
                    use_container_width=True,
                )

            if confirmare:
                termen = cautare_produs.strip()

                if not termen:
                    st.warning("Scrie numele produsului înainte de Enter.")
                else:
                    rezultate = cauta_produse(termen)

                    if not rezultate:
                        st.error(
                            f"Produsul «{termen}» nu există în Admin Produse."
                        )
                    elif len(rezultate) == 1:
                        nume, valoare = rezultate[0]
                        adauga_produs_la_target(nume, valoare)
                        st.success(
                            f"✓ {nume} adăugat la target: +{valoare:.2f} lei"
                        )
                        st.rerun()
                    else:
                        st.warning(
                            "Am găsit mai multe produse. Scrie un nume mai exact și apasă Enter."
                        )
                        for nume, valoare in rezultate:
                            st.write(f"• **{nume}** — {valoare:.2f} lei")

            target_items = st.session_state.get("target_items", {})
            if target_items:
                st.divider()
                st.write("**Produse adăugate la target:**")

                produse_admin = incarca_produse()
                for nume, cantitate in list(target_items.items()):
                    try:
                        valoare = float(produse_admin[nume])
                    except (KeyError, TypeError, ValueError):
                        continue

                    subtotal = valoare * int(cantitate)
                    c_prod, c_minus, c_plus = st.columns([0.65, 0.17, 0.18])

                    c_prod.write(
                        f"**{nume}** × {int(cantitate)} — {subtotal:.2f} lei"
                    )

                    if c_minus.button(
                        "➖",
                        key=f"target_minus_{nume}",
                        use_container_width=True,
                    ):
                        elimina_produs_din_target(nume, valoare)
                        st.rerun()

                    if c_plus.button(
                        "➕",
                        key=f"target_plus_{nume}",
                        use_container_width=True,
                    ):
                        adauga_produs_la_target(nume, valoare)
                        st.rerun()

            if st.button("RESET TARGET", key="reset_target_products", use_container_width=True):
                s["target_manual_val"] = 0.0
                s["target_items"] = {}
                st.session_state["target_items"] = {}
                salveaza_sesiune(
                    s["start"],
                    s["actual"],
                    0.0,
                    s.get("tura_activa"),
                    {},
                )
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
             salveaza_sesiune(s.get('start', 0), s.get('actual', 0), s.get('target_manual_val', 0.0), s['tura_activa'])
             trimite_pe_telegram(f"🟢 *Check-in efectuat*\nTura a început la ora: `{timp_acum.strftime('%H:%M:%S')}`")
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
                
                trimite_pe_telegram(f"🔴 *Check-out efectuat*\nTura s-a încheiat. Total ore lucrate: *{ore_lucrate} ore*")
                
                s['tura_activa'] = None
                salveaza_sesiune(s.get('start', 0), s.get('actual', 0), 0.0, None)
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
# 5. TAB CENTRALIZATOR & STATISTICI
# ==========================================
with tab_centr:
    st.subheader("📊 Analiză & Istoric Ture")
    
    # --- ZONĂ ADĂUGARE RAPORT MANUAL ---
    with st.expander("➕ Adaugă Manual un Raport în Centralizator", expanded=False):
        st.write("Introdu detaliile unei ture pentru a o adăuga permanent în baza de date:")
        with st.form("formular_raport_manual"):
            data_manuala = st.date_input("Data raportului:", value=datetime.now(ZoneInfo("Europe/Bucharest")))
            comenzi_manuale = st.number_input("Număr comenzi:", min_value=0, value=10, step=1)
            target_manual = st.number_input("Valoare target (lei):", min_value=0.0, value=50.0, step=0.5, format="%.2f")
            
            buton_salvare_manual = st.form_submit_button("💾 Salvează în Baza de Date")
            if buton_salvare_manual:
                rapoarte = incarca_rapoarte_json()
                rapoarte.append({
                    "id": datetime.now().strftime("%Y%m%d%H%M%S"),
                    "Data": data_manuala.strftime("%d.%m.%Y"),
                    "Comenzi": int(comenzi_manuale),
                    "Target": float(target_manual)
                })
                salveaza_rapoarte_json(rapoarte)
                
                trimite_pe_telegram(f"📝 *Raport adăugat manual*\n📅 Data: {data_manuala.strftime('%d.%m.%Y')}\n📦 Comenzi: {comenzi_manuale}\n🎯 Target: {target_manual:.2f} lei")
                st.success("Raportul a fost adăugat cu succes!")
                st.rerun()

    lista_rapoarte = incarca_rapoarte_json()
    total_com = sum(r['Comenzi'] for r in lista_rapoarte)
    total_tgt = sum(r['Target'] for r in lista_rapoarte)

    col_m1, col_m2 = st.columns(2)
    col_m1.metric("Total Comenzi", total_com)
    col_m2.metric("Total Target", f"{total_tgt:.2f} lei")
    
    if lista_rapoarte:
        st.divider()
        df_rapoarte = pd.DataFrame(lista_rapoarte)
        
        if st.button("📤 Trimite Centralizatorul pe Telegram", use_container_width=True):
            mesaj_centralizator = f"📊 *CENTRALIZATOR COMENZI PRESTO*\n\n"
            mesaj_centralizator += f"📦 *Total Comenzi:* {total_com}\n"
            mesaj_centralizator += f"🎯 *Total Target:* {total_tgt:.2f} lei\n\n"
            mesaj_centralizator += "📋 *Istoric Ture:*\n"
            
            for r in lista_rapoarte:
                mesaj_centralizator += f"• Data: {r['Data']} | Comenzi: {r['Comenzi']} | Target: {r['Target']:.2f} lei\n"
            
            succes_tg = trimite_pe_telegram(mesaj_centralizator)
            if succes_tg:
                st.success("Centralizatorul a fost trimis cu succes pe Telegram sub formă de text!")
            else:
                st.error("A eșuat trimiterea. Verifică datele din Secrets.")
        
        st.divider()
        df_grafic = df_rapoarte.groupby("Data")["Comenzi"].sum().reset_index()
        st.write("📈 **Evoluție Comenzi Zilnice**")
        st.bar_chart(df_grafic, x="Data", y="Comenzi", color="#ff4b4b")
        
        st.divider()
        st.write("📋 **Istoric Detaliat Ture (Editează sau Șterge)**")
        
        for rand in lista_rapoarte:
            with st.container(border=True):
                c_info, c_ed, c_del = st.columns([0.6, 0.2, 0.2])
                c_info.write(f"📄 **{rand['Data']}** | {rand['Comenzi']} com | {rand['Target']:.2f} lei")
                
                editeaza_apasat = c_ed.button("✏️ Editează", key=f"edit_btn_{rand['id']}")
                
                if c_del.button("❌ Șterge", key=f"del_{rand['id']}"): 
                    lista_rapoarte = [r for r in lista_rapoarte if r['id'] != rand['id']]
                    salveaza_rapoarte_json(lista_rapoarte)
                    st.rerun()
                
                if editeaza_apasat:
                    st.session_state[f"is_editing_{rand['id']}"] = True
                
                if st.session_state.get(f"is_editing_{rand['id']}", False):
                    with st.form(key=f"form_edit_{rand['id']}"):
                        st.write(f"Modificare raport din data: {rand['Data']}")
                        
                        data_curenta_obj = datetime.strptime(rand['Data'], "%d.%m.%Y")
                        noua_data = st.date_input("Data raportului:", value=data_curenta_obj, key=f"d_inp_{rand['id']}")
                        
                        nou_com = st.number_input("Comenzi:", value=rand['Comenzi'], step=1, key=f"c_inp_{rand['id']}")
                        nou_tgt = st.number_input("Target (lei):", value=rand['Target'], format="%.2f", step=0.1, key=f"t_inp_{rand['id']}")
                        
                        col_salveaza, col_anuleaza = st.columns(2)
                        if col_salveaza.form_submit_button("Salvează Modificările"):
                            for r in lista_rapoarte:
                                if r['id'] == rand['id']:
                                    r['Data'] = noua_data.strftime("%d.%m.%Y")
                                    r['Comenzi'] = int(nou_com)
                                    r['Target'] = float(nou_tgt)
                            salveaza_rapoarte_json(lista_rapoarte)
                            st.session_state[f"is_editing_{rand['id']}"] = False
                            st.success("Modificat cu succes!")
                            st.rerun()
                            
                        if col_anuleaza.form_submit_button("Anulează"):
                            st.session_state[f"is_editing_{rand['id']}"] = False
                            st.rerun()
    else:
        st.info("Nu există rapoarte salvate încă în baza de date. Finalizează o tură sau adaugă un raport manual mai sus.")

# ==========================================
# 6. TAB ADMIN PRODUSE
# ==========================================
with tab_admin:
    st.subheader("🛠️ Administrare Produse")
    st.caption(
        "Aceasta este lista folosită de Target. Dispeceratul caută exclusiv produsele de aici."
    )

    produse = incarca_produse()

    with st.form("admin_produs_nou", clear_on_submit=True):
        st.write("### ➕ Adaugă produs")
        col_nume, col_valoare = st.columns([0.7, 0.3])
        nume_nou = col_nume.text_input("Nume produs:")
        valoare_noua = col_valoare.number_input(
            "Valoare target:",
            min_value=0.0,
            step=0.1,
            format="%.2f",
        )

        if st.form_submit_button("Adaugă produs", type="primary"):
            nume_nou = " ".join(nume_nou.strip().split())
            if not nume_nou:
                st.error("Introdu numele produsului.")
            elif nume_nou in produse:
                st.error("Produsul există deja în Admin Produse.")
            else:
                produse[nume_nou] = float(valoare_noua)
                salveaza_produse(produse)
                st.success(f"Produsul «{nume_nou}» a fost adăugat.")
                st.rerun()

    st.divider()
    st.write("### 📋 Produse existente")

    if not produse:
        st.info("Nu există produse în produse.json.")
    else:
        for nume in sorted(produse, key=str.lower):
            try:
                valoare = float(produse[nume])
            except (TypeError, ValueError):
                continue

            c_nume, c_val, c_save, c_del = st.columns([0.42, 0.18, 0.20, 0.20])
            c_nume.write(f"**{nume}**")

            valoare_noua = c_val.number_input(
                "Valoare",
                min_value=0.0,
                value=valoare,
                step=0.1,
                format="%.2f",
                key=f"admin_value_{nume}",
                label_visibility="collapsed",
            )

            if c_save.button("💾 Salvează", key=f"admin_save_{nume}"):
                produse[nume] = float(valoare_noua)
                salveaza_produse(produse)
                st.success(f"Valoarea pentru «{nume}» a fost actualizată.")
                st.rerun()

            if c_del.button("🗑️ Șterge", key=f"admin_delete_{nume}"):
                produse.pop(nume, None)
                salveaza_produse(produse)
                st.success(f"Produsul «{nume}» a fost șters din Admin.")
                st.rerun()
