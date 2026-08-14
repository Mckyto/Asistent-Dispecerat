import streamlit as st
import sqlite3

# --- CONFIGURARE BAZĂ DE DATE ---
DB_NAME = "presto.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS produse (id INTEGER PRIMARY KEY, nume TEXT UNIQUE, valoare REAL)")
    c.execute("CREATE TABLE IF NOT EXISTS sesiune (id INTEGER PRIMARY KEY, start INTEGER, actual INTEGER, target REAL)")
    c.execute("INSERT OR IGNORE INTO sesiune (id, start, actual, target) VALUES (1, 0, 0, 0)")
    conn.commit()
    conn.close()

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

# --- UI ---
st.set_page_config(page_title="Presto Dispecerat", layout="centered")
init_db()

st.title("🍕 Dispecerat Presto")

tab_disp, tab_admin = st.tabs(["⚙️ Dispecerat", "📦 Admin Produse"])

# --- TAB 1: DISPECERAT ---
with tab_disp:
    s = get_data()
    c1, c2 = st.columns(2)
    new_start = c1.number_input("Start:", value=int(s['start']), step=1)
    new_actual = c2.number_input("Actual:", value=int(s['actual']), step=1)

    if new_start != s['start'] or new_actual != s['actual']:
        update_session(new_start, new_actual, s['target'])
        st.rerun()

    st.info(f"📦 Comenzi totale: {new_actual - new_start}")

    st.subheader("🎯 Adăugare Target")
    with st.form("search_form", clear_on_submit=False):
        query = st.text_input("Scrie produsul și apasă Enter:")
        submit = st.form_submit_button("Caută")

    if submit and query:
        conn = sqlite3.connect(DB_NAME)
        res = conn.execute("SELECT * FROM produse WHERE nume LIKE ?", (f"%{query}%",)).fetchall()
        conn.close()
        if len(res) == 1:
            update_session(new_start, new_actual, s['target'] + res[0][2])
            st.success(f"Adăugat: {res[0][1]} (+{res[0][2]} lei)")
            st.rerun()
        elif len(res) > 1:
            st.session_state['res_list'] = res
        else:
            st.error("Produs negăsit.")

    if 'res_list' in st.session_state:
        optiuni = {f"{p[1]} ({p[2]} lei)": p for p in st.session_state['res_list']}
        sel = st.selectbox("Alege produsul:", options=list(optiuni.keys()))
        if st.button("Confirmă"):
            p_ales = optiuni[sel]
            update_session(new_start, new_actual, s['target'] + p_ales[2])
            del st.session_state['res_list']
            st.rerun()

    st.metric("🎯 Target Acumulat", f"{s['target']:.2f} lei")
    if st.button("Reset Target"):
        update_session(new_start, new_actual, 0.0)
        st.rerun()

# --- TAB 2: ADMIN PRODUSE ---
with tab_admin:
    st.subheader("➕ Adaugă Produs Nou")
    with st.form("new_prod"):
        n_nume = st.text_input("Nume Produs")
        n_val = st.number_input("Valoare (lei)", step=0.1)
        if st.form_submit_button("Salvează"):
            conn = sqlite3.connect(DB_NAME)
            try:
                conn.execute("INSERT INTO produse (nume, valoare) VALUES (?, ?)", (n_nume, n_val))
                conn.commit()
                st.success("Produs adăugat!")
                st.rerun()
            except: st.error("Eroare (posibil nume duplicat)")
            conn.close()

    st.divider()
    st.subheader("📋 Produse Existente")
    conn = sqlite3.connect(DB_NAME)
    prods = conn.execute("SELECT * FROM produse ORDER BY nume").fetchall()
    conn.close()
    
    for p in prods:
        c1, c2 = st.columns([0.8, 0.2])
        c1.write(f"**{p[1]}** — {p[2]} lei")
        if c2.button("Șterge", key=f"del_{p[0]}"):
            conn = sqlite3.connect(DB_NAME)
            conn.execute("DELETE FROM produse WHERE id=?", (p[0],))
            conn.commit()
            conn.close()
            st.rerun()
