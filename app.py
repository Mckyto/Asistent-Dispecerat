import streamlit as st
import sqlite3
from datetime import datetime

# --- CONFIGURARE BAZĂ DE DATE ---
DB_NAME = "presto.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Tabel produse
    c.execute("CREATE TABLE IF NOT EXISTS produse (id INTEGER PRIMARY KEY, nume TEXT, valoare REAL)")
    # Tabel sesiune (stare curentă)
    c.execute("CREATE TABLE IF NOT EXISTS sesiune (id INTEGER PRIMARY KEY, start INTEGER, actual INTEGER, target REAL)")
    # Inițializare sesiune dacă e goală
    c.execute("INSERT OR IGNORE INTO sesiune (id, start, actual, target) VALUES (1, 0, 0, 0)")
    conn.commit()
    conn.close()

# --- FUNCȚII AJUTĂTOARE ---
def get_data():
    conn = sqlite3.connect(DB_NAME)
    data = conn.execute("SELECT * FROM sesiune WHERE id=1").fetchone()
    conn.close()
    return {"start": data[1], "actual": data[2], "target": data[3]}

def update_session(start, actual, target):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("UPDATE sesiune SET start=?, actual=?, target=? WHERE id=1", (start, actual, target))
    conn.commit()
    conn.close()

# --- INTERFAȚA ---
st.set_page_config(page_title="Presto Dispecerat", layout="centered")
init_db()

st.title("🍕 Dispecerat Presto")

# Secțiune Dispecerat
s = get_data()

c1, c2 = st.columns(2)
new_start = c1.number_input("Start:", value=s['start'], step=1)
new_actual = c2.number_input("Actual:", value=s['actual'], step=1)

if new_start != s['start'] or new_actual != s['actual']:
    update_session(new_start, new_actual, s['target'])
    st.rerun()

st.info(f"Comenzi totale: {new_actual - new_start}")

# Secțiune Target (Căutare + Enter)
st.subheader("🎯 Adăugare Target")

with st.form("search_form", clear_on_submit=True):
    query = st.text_input("Scrie produsul și apasă Enter:")
    submit = st.form_submit_button("Adaugă")

if submit and query:
    conn = sqlite3.connect(DB_NAME)
    res = conn.execute("SELECT * FROM produse WHERE nume LIKE ?", (f"%{query}%",)).fetchall()
    conn.close()
    
    if len(res) == 1:
        new_target = s['target'] + res[0][2]
        update_session(new_start, new_actual, new_target)
        st.success(f"Adăugat: {res[0][1]} (+{res[0][2]} lei)")
        st.rerun()
    elif len(res) > 1:
        st.warning(f"Prea multe rezultate pentru '{query}'. Fii mai specific.")
    else:
        st.error("Produs negăsit.")

st.metric("Target Acumulat", f"{s['target']:.2f} lei")

if st.button("Reset Target"):
    update_session(new_start, new_actual, 0.0)
    st.rerun()

# Sidebar - Administrare Produse
with st.sidebar:
    st.header("⚙️ Produse")
    with st.form("add_prod"):
        nume_prod = st.text_input("Nume:")
        val_prod = st.number_input("Valoare:", step=0.5)
        if st.form_submit_button("Salvează Produs"):
            conn = sqlite3.connect(DB_NAME)
            conn.execute("INSERT INTO produse (nume, valoare) VALUES (?, ?)", (nume_prod, val_prod))
            conn.commit()
            conn.close()
            st.rerun()
