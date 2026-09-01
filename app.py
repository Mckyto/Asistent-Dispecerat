import requests
import streamlit as st
import pandas as pd

# URL-ul Web App obținut de la Pasul 1 (înlocuiește cu link-ul tău)
GOOGLE_SCRIPT_URL = "AICI_PUPI_LINKUL_PRIMIT_DE_LA_GOOGLE_APPS_SCRIPT"

# --- CONFIGURARE GENERALĂ ---
st.set_page_config(
    page_title="Presto & Livratori Hub", page_icon="🍕", layout="wide"
)
st.title("🍕 Panou Central: Presto & Livratori")

# Restul datelor inițiale...
SHEET_ID = "1HW_N9cu_6TkQ0Sv3DNIl0ZNVdslFmtXGj-sOCjZQS_Q"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"


@st.cache_data(ttl=5)
def incarca_date_livratori():
  try:
    df = pd.read_csv(SHEET_URL)
    df = df.dropna(how="all")
    return df
  except Exception as e:
    st.error(f"Eroare la citirea datelor: {e}")
    return pd.DataFrame()


if "livratori_modificati" not in st.session_state:
  df_google = incarca_date_livratori()
  st.session_state["livratori_modificati"] = df_google.copy()

# --- TABURI ---
tab_livratori, tab_disp, tab_admin = st.tabs(
    ["🛵 Gestionare Livratori", "⚙️ Dispecerat", "📦 Admin Produse"]
)

with tab_livratori:
  st.header("🛵 Gestionare Livratori")

  with st.expander("➕ Adaugă livrator nou"):
    with st.form("form_add", clear_on_submit=True):
      c1, c2 = st.columns(2)
      nume_nou = c1.text_input("Nume:")
      tel_nou = c2.text_input("Telefon:")

      if st.form_submit_button("Salvează livrator"):
        if nume_nou.strip() and tel_nou.strip():
          valoare_inserata = f"{nume_nou.strip()} - {tel_nou.strip()}"

          # Trimitem datele direct prin Web App-ul din Google Sheets (Fără 2FA, Fără Google Cloud!)
          try:
            response = requests.post(
                GOOGLE_SCRIPT_URL, json={"nume": valoare_inserata}
            )
            if response.status_code == 200:
              st.success(
                  f"Livratorul '{nume_nou}' a fost adăugat și în Google Sheet!"
              )
            else:
              st.warning(
                  "Salvat local, dar a apărut o problemă cu Google Sheet."
              )
          except Exception as e:
            st.error(f"Eroare de conexiune: {e}")

          # Actualizare locală în sesiune
          cols = list(st.session_state["livratori_modificati"].columns)
          col_nume = cols[0] if len(cols) > 0 else "Nume"
          nou_rand = pd.DataFrame([{col_nume: valoare_inserata}])
          st.session_state["livratori_modificati"] = pd.concat(
              [st.session_state["livratori_modificati"], nou_rand],
              ignore_index=True,
          )
          st.rerun()
        else:
          st.warning("Te rog să completezi ambele câmpuri.")

  # (Restul codului de căutare rămâne la fel...)
