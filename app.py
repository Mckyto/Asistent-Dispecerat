import streamlit as st
import sqlite3

# --- CONFIGURARE BAZĂ DE DATE ---
DB_NAME = "presto.db"

# Lista cu produsele și valorile preluate din imagine
PRODUSE_INITIALE = [
    ("Baclava", 1.0),
    ("Tiramisu", 1.0),
    ("Cheesecake", 1.0),
    ("Kataif", 1.0),
    ("Placinta cu iaurt/cu mere", 1.0),
    ("Salam de biscuiti", 1.0),
    ("Gogosi", 1.0),
    ("Bucket gogosi", 1.0),
    ("Inghetata", 1.0),
    ("Limonada", 1.0),
    ("Hamburger pui", 0.5),
    ("Painica mare", 0.2),
    ("Paste Quattro Formaggi", 0.5),
    ("Pizza Napoletta", 1.0),
    ("Painica napolettana", 1.0),
    ("Pita Gyros", 0.5),
    ("Bere Porst", 1.0),
    ("Shaorma cu pui crispy", 0.5),
    ("Salata de pui crispy", 0.5),
    ("Mozzarella", 0.3),
    ("Grana padano", 0.3),
    ("Lapte tibetana", 1.0),
    ("Pui ZAO", 1.0),
    ("Mix de fructe prajit/in caramel", 1.0),
    ("Pui sichuan", 1.0),
    ("Wings bucket", 2.0),
    ("Apa BAX", 2.0)
]

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Creare tabele
    c.execute("CREATE TABLE IF NOT EXISTS produse (id INTEGER PRIMARY KEY, nume TEXT UNIQUE, valoare REAL)")
    c.execute("CREATE TABLE IF NOT EXISTS sesiune (id INTEGER PRIMARY KEY, start INTEGER, actual INTEGER, target REAL)")
    
    # Sesiune inițială
    c.execute("INSERT OR IGNORE INTO sesiune (id, start, actual, target) VALUES (1, 0, 0, 0)")
    
    # Populare automată produse dacă tabela e goală sau adăugare lipsuri
    for nume, valoare in PRODUSE_INITIALE:
        c.execute("INSERT OR IGNORE INTO produse (nume, valoare) VALUES (?, ?)", (nume, valoare))
        
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

s = get_data()

# Secțiune Dispecerat (Start / Actual)
c1, c2 = st.columns(2)
new_start = c1.number_input("Start:", value=s['start'], step=1)
new_actual = c2.number_input("Actual:", value=s['actual'], step=1)

if new_start != s['start'] or new_actual != s['actual']:
    update_session(new_start, new_actual, s['target'])
    st.rerun()

st.info(f"📦 Comenzi totale: {new_actual - new_start}")

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
        st.warning(f"S-au găsit mai multe produse pentru '{query}':")
        for p in res:
            st.write(f"- **{p[1]}** ({p[2]} lei)")
    else:
        st.error("Produs negăsit.")

st.metric("🎯 Target Acumulat", f"{s['target']:.2f} lei")

if st.button("Reset Target"):
    update_session(new_start, new_actual, 0.0)
    st.rerun()

# Sidebar - Vizualizare produse existente
with st.sidebar:
    st.header("📋 Produse în Sistem")
    conn = sqlite3.connect(DB_NAME)
    produse_db = conn.execute("SELECT nume, valoare FROM produse ORDER BY nume").fetchall()
    conn.close()
    
    for p in produse_db:
        st.caption(f"• {p[0]} — **{p[1]} lei**")
