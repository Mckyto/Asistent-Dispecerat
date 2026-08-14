import streamlit as st

# --- CONFIGURARE ---
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

# --- UI ---import streamlit as st

# --- CONFIGURARE ---
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

# --- UI ---
st.set_page_config(page_title="Presto Dispecerat", layout="centered")

st.title("🍕 Dispecerat Presto")

# Inițializare stare în memorie (fără baza de date / fără salvare persistentă)
if 'start' not in st.session_state:
    st.session_state['start'] = 0
if 'actual' not in st.session_state:
    st.session_state['actual'] = 0
if 'target' not in st.session_state:
    st.session_state['target'] = 0.0

if 'produse_custom' not in st.session_state:
    st.session_state['produse_custom'] = {nume: val for nume, val in PRODUSE_INITIALE}

tab_disp, tab_admin = st.tabs(["⚙️ Dispecerat", "📦 Admin Produse"])

# --- TAB DISPECERAT ---
with tab_disp:
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

# --- TAB ADMIN ---
with tab_admin:
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
        if col_d.button("Șterge", key=f"del_{nume}"):
            del st.session_state['produse_custom'][nume]
            st.rerun()
st.set_page_config(page_title="Presto Dispecerat", layout="centered")

st.title("🍕 Dispecerat Presto")

# Inițializare stare în memorie (fără baza de date / fără salvare persistentă)
if 'start' not in st.session_state:
    st.session_state['start'] = 0
if 'actual' not in st.session_state:
    st.session_state['actual'] = 0
if 'target' not in st.session_state:
    st.session_state['target'] = 0.0

if 'produse_custom' not in st.session_state:
    st.session_state['produse_custom'] = {nume: val for nume, val in PRODUSE_INITIALE}

tab_disp, tab_admin = st.tabs(["⚙️ Dispecerat", "📦 Admin Produse"])

# --- TAB DISPECERAT ---
with tab_disp:
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

# --- TAB ADMIN ---
with tab_admin:
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
        if col_d.button("Șterge", key=f"del_{nume}"):
            del st.session_state['produse_custom'][nume]
            st.rerun()
