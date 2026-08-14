import streamlit as st
import sqlite3

# --- CONFIGURARE ---
DB_NAME = "presto.db"

PRODUSE_INITIALE = [
    ("Baclava", 1.0), ("Tiramisu", 1.0), ("Cheesecake", 1.0), ("Kataif", 1.0),
    ("Placinta cu iaurt/cu mere", 1.0), ("Salam de biscuiti", 1.0), ("Gogosi", 1.0),
    ("Bucket gogosi", 1.0), ("Inghetata", 1.0), ("Limonada", 1.0), ("Hamburger pui", 0.5),
    ("Painica mare", 0.2), ("Paste Quattro Formaggi", 0.5), ("Pizza Napoletta", 1.0),
    ("Painica napolettana", 1.0), ("Pita Gyros", 0.5), ("Bere Porst", 1.0),
    ("Shaorma cu pui crispy", 0.5), ("Salata de pui crispy", 0.5), ("Mozzarella", 0.3),
    ("Grana padano", 0.3), ("Lapte tibetana", 1.0), ("Pui ZAO", 1.0),
    ("Mix de fructe prajit/in caramel", 1.0), ("Pui sichuan", 1.0), ("Wings bucket", 2.0),
    ("Apa BAX", 2.0)
]

def init_db():
    conn = sqlite3.connect(DB_NAME, timeout=20)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS produse (id INTEGER PRIMARY KEY, nume TEXT UNIQUE, valoare REAL)")
    c.execute("CREATE TABLE IF NOT EXISTS sesiune (id INTEGER PRIMARY KEY, start INTEGER, actual INTEGER, target REAL)")
    c.execute("INSERT OR IGNORE INTO sesiune (id, start, actual, target) VALUES (1, 0, 0, 0)")
    for nume, valoare in PRODUSE_INITIALE:
        try:
            c.execute("INSERT INTO produse (nume, valoare) VALUES (?, ?)", (nume, valoare))
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    conn.close()

def get_data():
    conn = sqlite3.connect(DB_NAME, timeout=20)
    data = conn.execute("SELECT * FROM sesiune WHERE id=1").fetchone()
    conn.close()
    return {"start": data[1], "actual": data[2], "target": data[3]}

def update_session(start, actual, target):
    conn = sqlite3.connect(DB_NAME, timeout=20)
    conn.execute("UPDATE sesiune SET start=?, actual=?, target=? WHERE id=1", (start, actual, target))
    conn.commit()
    conn.close()

# --- UI ---
st.set_page_config(page_title="Presto Dispecerat", layout="centered")
init_db()

st.title("🍕 Dispecerat Presto")
s = get_data()

tab_disp, tab_admin = st.tabs(["⚙️ Dispecerat", "📦 Admin Produse"])

# --- TAB DISPECERAT ---
with tab_disp:
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
        conn = sqlite3.connect(DB_NAME, timeout=20)
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
        res = st.session_state['res_list']
        optiuni = {f"{p[1]} ({p[2]} lei)": p for p in res}
        sel = st.selectbox("Alege produsul:", options=list(optiuni.keys()))
        if st.button("Confirmă Adăugarea"):
            p_ales = optiuni[sel]
            update_session(new_start, new_actual, s['target'] + p_ales[2])
            del st.session_state['res_list']
            st.rerun()

    st.metric("🎯 Target Acumulat", f"{s['target']:.2f} lei")
    if st.button("Reset Target"):
        update_session(new_start, new_actual, 0.0)
        st.rerun()

# --- TAB ADMIN ---
with tab_admin:
    st.subheader("➕ Adaugă Produs Nou")
    with st.form("new_prod", clear_on_submit=True):
        n_nume = st.text_input("Nume Produs")
        n_val = st.number_input("Valoare (lei)", step=0.1, min_value=0.0)
        if st.form_submit_button("Salvează"):
            if n_nume.strip():
                conn = sqlite3.connect(DB_NAME, timeout=20)
                try:
                    conn.execute("INSERT INTO produse (nume, valoare) VALUES (?, ?)", (n_nume.strip(), n_val))
                    conn.commit()
                    st.success("Produs adăugat!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Eroare: Produsul există deja!")
                finally:
                    conn.close()

    st.divider()
    st.subheader("📋 Produse Existente")
    conn = sqlite3.connect(DB_NAME, timeout=20)
    prods = conn.execute("SELECT * FROM produse ORDER BY nume").fetchall()
    conn.close()
    
    for p in prods:
        col_n, col_v, col_d = st.columns([0.5, 0.3, 0.2])
        col_n.write(p[1])
        col_v.write(f"{p[2]:.2f} lei")
        if col_d.button("Șterge", key=f"del_{p[0]}"):
            conn = sqlite3.connect(DB_NAME, timeout=20)
            conn.execute("DELETE FROM produse WHERE id=?", (p[0],))
            conn.commit()
            conn.close()
            st.rerun()
