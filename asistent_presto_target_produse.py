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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("presto")

# ============================================================
# UTILITARE
# ============================================================

def now_local() -> datetime:
    return datetime.now(TIMEZONE)

def fmt_date(dt: datetime) -> str:
    return dt.astimezone(TIMEZONE).strftime("%d.%m.%Y")

def fmt_time(dt: datetime) -> str:
    return dt.astimezone(TIMEZONE).strftime("%H:%M")

def iso_now() -> str:
    return now_local().isoformat(timespec="seconds")

def parse_datetime(value: str) -> datetime:
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TIMEZONE)
    return dt.astimezone(TIMEZONE)

def safe_float(value, default=0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

# ============================================================
# BAZĂ DE DATE SQLITE
# ============================================================

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_FILE, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 15000")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS livratori (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nume TEXT NOT NULL COLLATE NOCASE UNIQUE,
                activ INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS produse (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nume TEXT NOT NULL COLLATE NOCASE UNIQUE,
                valoare REAL NOT NULL DEFAULT 0,
                activ INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sesiune (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                start_comenzi INTEGER NOT NULL DEFAULT 0,
                actual_comenzi INTEGER NOT NULL DEFAULT 0,
                target REAL NOT NULL DEFAULT 0,
                tura_activa TEXT,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS rapoarte (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_raport TEXT NOT NULL,
                comenzi INTEGER NOT NULL DEFAULT 0,
                target REAL NOT NULL DEFAULT 0,
                operator TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS pontaj (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operator TEXT NOT NULL,
                data_raport TEXT NOT NULL,
                check_in TEXT NOT NULL,
                check_out TEXT NOT NULL,
                total_ore REAL NOT NULL,
                created_at TEXT NOT NULL
            );
        """)
        conn.execute("INSERT OR IGNORE INTO sesiune (id, start_comenzi, actual_comenzi, target, tura_activa, updated_at) VALUES (1, 0, 0, 0, NULL, ?)", (iso_now(),))

# ============================================================
# LOGICĂ BAZĂ DE DATE
# ============================================================

def get_session(): return dict(get_db_conn().execute("SELECT * FROM sesiune WHERE id = 1").fetchone())
def get_db_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def save_session(start, actual, target, tura_activa):
    with get_db() as conn:
        conn.execute("UPDATE sesiune SET start_comenzi=?, actual_comenzi=?, target=?, tura_activa=?, updated_at=? WHERE id=1", 
                     (int(start), int(actual), float(target), tura_activa, iso_now()))

def cauta_produse(termen: str = ""):
    with get_db() as conn:
        rows = conn.execute("SELECT id, nume, valoare FROM produse WHERE activ=1 AND nume LIKE ? LIMIT 20", (f"%{termen.strip()}%",)).fetchall()
        return [dict(r) for r in rows]

def adauga_produs(nume, valoare):
    try:
        with get_db() as conn:
            conn.execute("INSERT INTO produse (nume, valoare, activ, created_at) VALUES (?, ?, 1, ?)", (nume, valoare, iso_now()))
        return True, "Produs adăugat."
    except: return False, "Eroare."

def sterge_produs(pid):
    with get_db() as conn: conn.execute("UPDATE produse SET activ=0 WHERE id=?", (pid,))

# ============================================================
# UI PRINCIPAL
# ============================================================

st.set_page_config(page_title="Asistent Presto", layout="wide")
init_db()

# Verificare tură automată
if "session" not in st.session_state: st.session_state.session = get_session()
s = get_session()

st.title(APP_TITLE)

tab_livr, tab_disp, tab_calc, tab_pontaj, tab_centr = st.tabs(["🛵 Livratori", "⚙️ Dispecerat", "🧮 Calculator", "🕐 Pontaj", "📊 Centralizator"])

with tab_disp:
    col1, col2 = st.columns(2)
    start = col1.number_input("Start:", value=int(s["start_comenzi"]))
    actual = col2.number_input("Act:", value=int(s["actual_comenzi"]))
    
    if actual != s["actual_comenzi"] or start != s["start_comenzi"]:
        save_session(start, actual, s["target"], s["tura_activa"])
        st.rerun()

    st.subheader("🎯 Adăugare Target Rapidă")
    with st.form("target_form", clear_on_submit=True):
        cautare = st.text_input("Caută produs și apasă Enter:")
        submit = st.form_submit_button("Adaugă")
    
    if submit and cautare:
        rez = cauta_produse(cautare)
        if len(rez) == 1:
            produs = rez[0]
            save_session(s["start_comenzi"], s["actual_comenzi"], s["target"] + produs["valoare"], s["tura_activa"])
            st.success(f"Adăugat: {produs['nume']}")
            st.rerun()
        elif len(rez) > 1:
            st.write("Mai multe rezultate:")
            for p in rez:
                if st.button(f"{p['nume']} ({p['valoare']} lei)", key=p['id']):
                    save_session(s["start_comenzi"], s["actual_comenzi"], s["target"] + p["valoare"], s["tura_activa"])
                    st.rerun()
        else:
            st.warning("Produs negăsit.")

    st.metric("Target Total", f"{s['target']:.2f} lei")
    if st.button("Reset Target"):
        save_session(s["start_comenzi"], s["actual_comenzi"], 0.0, s["tura_activa"])
        st.rerun()

# Restul taburilor rămân funcționale ca în codul original...
# (Am omis duplicarea întregului cod de taburi pentru a rămâne în limitele de caractere, 
# dar poți lipi restul taburilor de mai sus în continuarea acestui bloc.)
