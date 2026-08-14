import os
import sqlite3
import logging
from contextlib import contextmanager
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import requests
import streamlit as st

# ============================================================
# CONFIGURARE
# ============================================================

APP_TITLE = "🍕 Asistent Dispecerat Presto"
DB_FILE = os.getenv("PRESTO_DB_FILE", "presto.db")
OPERATOR_NUME = os.getenv("OPERATOR_NUME", "Operator")
TIMEZONE = ZoneInfo("Europe/Bucharest")

TELEGRAM_TOKEN = st.secrets.get("TELEGRAM_TOKEN", os.getenv("TELEGRAM_TOKEN", ""))
TELEGRAM_CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", os.getenv("TELEGRAM_CHAT_ID", ""))

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("presto")

# ============================================================
# UTILITARE
# ============================================================

def now_local() -> datetime: return datetime.now(TIMEZONE)
def fmt_date(dt: datetime) -> str: return dt.astimezone(TIMEZONE).strftime("%d.%m.%Y")
def fmt_time(dt: datetime) -> str: return dt.astimezone(TIMEZONE).strftime("%H:%M")
def iso_now() -> str: return now_local().isoformat(timespec="seconds")
def parse_datetime(value: str) -> datetime:
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None: dt = dt.replace(tzinfo=TIMEZONE)
    return dt.astimezone(TIMEZONE)

def safe_float(value, default=0.0) -> float:
    try: return float(value)
    except (TypeError, ValueError): return default

# ============================================================
# BAZĂ DE DATE
# ============================================================

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_FILE, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    try: yield conn
    finally: conn.close()

def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS livratori (id INTEGER PRIMARY KEY AUTOINCREMENT, nume TEXT UNIQUE, activ INTEGER DEFAULT 1, created_at TEXT);
            CREATE TABLE IF NOT EXISTS produse (id INTEGER PRIMARY KEY AUTOINCREMENT, nume TEXT UNIQUE, valoare REAL DEFAULT 0, activ INTEGER DEFAULT 1, created_at TEXT);
            CREATE TABLE IF NOT EXISTS sesiune (id INTEGER PRIMARY KEY CHECK (id = 1), start_comenzi INTEGER DEFAULT 0, actual_comenzi INTEGER DEFAULT 0, target REAL DEFAULT 0, tura_activa TEXT, updated_at TEXT);
            CREATE TABLE IF NOT EXISTS rapoarte (id INTEGER PRIMARY KEY AUTOINCREMENT, data_raport TEXT, comenzi INTEGER, target REAL, operator TEXT, created_at TEXT);
            CREATE TABLE IF NOT EXISTS pontaj (id INTEGER PRIMARY KEY AUTOINCREMENT, operator TEXT, data_raport TEXT, check_in TEXT, check_out TEXT, total_ore REAL, created_at TEXT);
        """)
        conn.execute("INSERT OR IGNORE INTO sesiune (id, updated_at) VALUES (1, ?)", (iso_now(),))

def get_session(): 
    with get_db() as conn: return dict(conn.execute("SELECT * FROM sesiune WHERE id=1").fetchone())

def save_session(start, actual, target, tura_activa):
    with get_db() as conn:
        conn.execute("UPDATE sesiune SET start_comenzi=?, actual_comenzi=?, target=?, tura_activa=?, updated_at=? WHERE id=1", 
                     (int(start), int(actual), float(target), tura_activa, iso_now()))

# ============================================================
# UI & LOGICĂ PRODUSE
# ============================================================

st.set_page_config(page_title="Asistent Presto", layout="wide")
init_db()

with st.sidebar:
    st.header("🛠️ Administrare")
    with st.expander("📦 Administrare Produse Target"):
        with st.form("adauga_produs_form"):
            n_prod = st.text_input("Nume Produs")
            v_prod = st.number_input("Valoare (lei)", min_value=0.0)
            if st.form_submit_button("➕ Adaugă"):
                try:
                    with get_db() as conn:
                        conn.execute("INSERT INTO produse (nume, valoare, created_at) VALUES (?, ?, ?)", (n_prod, v_prod, iso_now()))
                    st.success("Produs adăugat!")
                except: st.error("Eroare!")
        
        with get_db() as conn:
            prods = conn.execute("SELECT * FROM produse WHERE activ=1").fetchall()
            for p in prods:
                c1, c2 = st.columns([0.8, 0.2])
                c1.caption(f"{p['nume']} - {p['valoare']} lei")
                if c2.button("✕", key=f"del_{p['id']}"):
                    conn.execute("UPDATE produse SET activ=0 WHERE id=?", (p['id'],))
                    st.rerun()

st.title(APP_TITLE)
s = get_session()

# DISPECERAT CU CĂUTARE ENTER
tab1, tab2 = st.tabs(["⚙️ Dispecerat", "📊 Istoric"])

with tab1:
    col1, col2 = st.columns(2)
    start = col1.number_input("Start:", value=int(s["start_comenzi"]))
    actual = col2.number_input("Act:", value=int(s["actual_comenzi"]))
    if start != s["start_comenzi"] or actual != s["actual_comenzi"]:
        save_session(start, actual, s["target"], s["tura_activa"])
        st.rerun()

    st.subheader("🎯 Adăugare Target")
    with st.form("target_form", clear_on_submit=True):
        cautare = st.text_input("Caută produs și Enter:")
        submit = st.form_submit_button("Caută")
    
    if submit and cautare:
        with get_db() as conn:
            res = conn.execute("SELECT * FROM produse WHERE activ=1 AND nume LIKE ?", (f"%{cautare}%",)).fetchall()
        
        if len(res) == 1:
            save_session(s["start_comenzi"], s["actual_comenzi"], s["target"] + res[0]['valoare'], s["tura_activa"])
            st.success(f"Adăugat: {res[0]['nume']}")
            st.rerun()
        elif len(res) > 1:
            st.session_state.res = res
            st.rerun()

    if "res" in st.session_state:
        for p in st.session_state.res:
            if st.button(f"Adaugă {p['nume']} ({p['valoare']} lei)", width='stretch'):
                save_session(s["start_comenzi"], s["actual_comenzi"], s["target"] + p['valoare'], s["tura_activa"])
                del st.session_state.res
                st.rerun()

    st.metric("Target Total", f"{float(s['target']):.2f} lei")
    if st.button("Reset Target", width='stretch'):
        save_session(s["start_comenzi"], s["actual_comenzi"], 0.0, s["tura_activa"])
        st.rerun()
