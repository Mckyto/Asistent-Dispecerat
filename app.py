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
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS livratori (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nume TEXT NOT NULL COLLATE NOCASE UNIQUE,
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

            CREATE INDEX IF NOT EXISTS idx_rapoarte_data
                ON rapoarte(data_raport);

            CREATE INDEX IF NOT EXISTS idx_pontaj_data
                ON pontaj(data_raport);
            """
        )

        conn.execute(
            """
            INSERT OR IGNORE INTO sesiune
            (id, start_comenzi, actual_comenzi, target, tura_activa, updated_at)
            VALUES (1, 0, 0, 0, NULL, ?)
            """,
            (iso_now(),),
        )


# ============================================================
# TELEGRAM
# ============================================================

def telegram_configured() -> bool:
    return bool(TELEGRAM_TOKEN and TELEGRAM_CHAT_ID)


def trimite_pe_telegram(mesaj: str) -> bool:
    if not telegram_configured():
        logger.warning("Telegram nu este configurat.")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mesaj,
        "parse_mode": "Markdown",
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except requests.RequestException as exc:
        logger.exception("Eroare Telegram: %s", exc)
        return False


# ============================================================
# SESIUNE / TURĂ
# ============================================================

def get_session() -> dict:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM sesiune WHERE id = 1"
        ).fetchone()

    return dict(row)


def save_session(start, actual, target, tura_activa):
    with get_db() as conn:
        conn.execute(
            """
            UPDATE sesiune
            SET start_comenzi = ?,
                actual_comenzi = ?,
                target = ?,
                tura_activa = ?,
                updated_at = ?
            WHERE id = 1
            """,
            (
                int(start),
                int(actual),
                float(target),
                tura_activa,
                iso_now(),
            ),
        )


def close_session():
    save_session(0, 0, 0.0, None)


# ============================================================
# LIVRATORI
# ============================================================

def cauta_livratori(termen: str = "") -> list[dict]:
    with get_db() as conn:
        if termen.strip():
            rows = conn.execute(
                """
                SELECT * FROM livratori
                WHERE activ = 1 AND nume LIKE ?
                ORDER BY nume COLLATE NOCASE
                """,
                (f"%{termen.strip()}%",),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM livratori
                WHERE activ = 1
                ORDER BY nume COLLATE NOCASE
                """
            ).fetchall()

    return [dict(row) for row in rows]


def adauga_livrator(nume: str) -> tuple[bool, str]:
    nume = " ".join(nume.strip().split())

    if len(nume) < 2:
        return False, "Numele este prea scurt."

    try:
        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO livratori (nume, activ, created_at)
                VALUES (?, 1, ?)
                """,
                (nume, iso_now()),
            )
        return True, f"Livratorul {nume} a fost adăugat."
    except sqlite3.IntegrityError:
        return False, "Acest livrator există deja."


def sterge_livrator(livrator_id: int):
    with get_db() as conn:
        conn.execute(
            "UPDATE livratori SET activ = 0 WHERE id = ?",
            (int(livrator_id),),
        )


# ============================================================
# RAPOARTE
# ============================================================

def adauga_raport(data_raport, comenzi, target):
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO rapoarte
            (data_raport, comenzi, target, operator, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                data_raport,
                int(comenzi),
                float(target),
                OPERATOR_NUME,
                iso_now(),
            ),
        )


def lista_rapoarte() -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM rapoarte
            ORDER BY id DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]


def actualizeaza_raport(raport_id, data_raport, comenzi, target):
    with get_db() as conn:
        conn.execute(
            """
            UPDATE rapoarte
            SET data_raport = ?, comenzi = ?, target = ?
            WHERE id = ?
            """,
            (
                data_raport,
                int(comenzi),
                float(target),
                int(raport_id),
            ),
        )


def sterge_raport(raport_id):
    with get_db() as conn:
        conn.execute(
            "DELETE FROM rapoarte WHERE id = ?",
            (int(raport_id),),
        )


# ============================================================
# PONTAJ
# ============================================================

def lista_pontaj() -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM pontaj
            ORDER BY id DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]


def adauga_pontaj(operator, data_raport, check_in, check_out, total_ore):
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO pontaj
            (operator, data_raport, check_in, check_out, total_ore, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                operator,
                data_raport,
                check_in,
                check_out,
                float(total_ore),
                iso_now(),
            ),
        )


def sterge_istoric_pontaj():
    with get_db() as conn:
        conn.execute("DELETE FROM pontaj")


# ============================================================
# ÎNCHIDERE TURĂ / RAPORTARE
# ============================================================

def finalizeaza_tura(motiv: str = "manual"):
    s = get_session()

    start = int(s["start_comenzi"])
    actual = int(s["actual_comenzi"])
    target = safe_float(s["target"])
    comenzi = max(0, actual - start)

    if s["tura_activa"]:
        timp_inceput = parse_datetime(s["tura_activa"])
    else:
        timp_inceput = now_local()

    adauga_raport(
        fmt_date(timp_inceput),
        comenzi,
        target,
    )

    if motiv == "automat":
        mesaj = (
            "⏰ *Tura automată (12h) s-a încheiat!*\n"
            f"👤 Operator: {OPERATOR_NUME}\n"
            f"📦 Comenzi totale: {comenzi}\n"
            f"🎯 Target total: {target:.2f} lei"
        )
    else:
        mesaj = (
            "✅ *RAPORT TURĂ Încheiată*\n"
            f"👤 Operator: {OPERATOR_NUME}\n"
            f"📦 Comenzi totale: *{comenzi}*\n"
            f"🎯 Target total acumulat: *{target:.2f} lei*"
        )

    trimite_pe_telegram(mesaj)

    if s["tura_activa"]:
        if motiv == "automat":
            timp_sfarsit = timp_inceput + timedelta(hours=12)
        else:
            timp_sfarsit = now_local()

        ore = 12.0 if motiv == "automat" else round(
            (timp_sfarsit - timp_inceput).total_seconds() / 3600, 2
        )

        adauga_pontaj(
            OPERATOR_NUME,
            fmt_date(timp_inceput),
            fmt_time(timp_inceput),
            fmt_time(timp_sfarsit) + (" (Auto 12h)" if motiv == "automat" else ""),
            ore,
        )

    close_session()


def verifica_tura_automata() -> bool:
    s = get_session()

    if not s["tura_activa"]:
        return False

    try:
        timp_inceput = parse_datetime(s["tura_activa"])
        if now_local() - timp_inceput >= timedelta(hours=12):
            finalizeaza_tura("automat")
            return True
    except (ValueError, TypeError):
        logger.exception("Tura activă are o valoare invalidă.")
        close_session()

    return False


# ============================================================
# EXPORT
# ============================================================

def rapoarte_dataframe() -> pd.DataFrame:
    data = lista_rapoarte()
    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)
    return df[
        ["id", "data_raport", "comenzi", "target", "operator", "created_at"]
    ]


def pontaj_dataframe() -> pd.DataFrame:
    data = lista_pontaj()
    if not data:
        return pd.DataFrame()

    return pd.DataFrame(data)


# ============================================================
# UI
# ============================================================

st.set_page_config(
    page_title="Asistent Presto",
    page_icon="🍕",
    layout="wide",
)

init_db()

# Verificarea automată se face la fiecare rerun.
if verifica_tura_automata():
    st.warning("⏰ Au trecut 12 ore. Tura a fost închisă și raportată automat.")
    st.rerun()

if "session" not in st.session_state:
    st.session_state.session = get_session()

s = get_session()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.header("🛠️ Setări & Teste")

    st.caption(f"Operator: {OPERATOR_NUME}")
    st.caption(f"Fus orar: Europe/Bucharest")

    if telegram_configured():
        st.success("Telegram configurat")
    else:
        st.warning(
            "Telegram nu este configurat. "
            "Aplicația funcționează în continuare fără notificări."
        )

    if st.button("🧪 Testează Bot Telegram", use_container_width=True):
        if not telegram_configured():
            st.error("Configurează TELEGRAM_TOKEN și TELEGRAM_CHAT_ID.")
        elif trimite_pe_telegram(
            "🤖 *Test reușit!* Botul Presto este activ."
        ):
            st.success("Mesajul a fost trimis.")
        else:
            st.error("Trimiterea a eșuat. Verifică tokenul și chat ID-ul.")


st.title(APP_TITLE)


# ============================================================
# TABURI
# ============================================================

tab_livr, tab_disp, tab_calc, tab_pontaj, tab_centr = st.tabs(
    [
        "🛵 Gestionare Livratori",
        "⚙️ Dispecerat & Target",
        "🧮 Calculator Procent",
        "🕐 Pontaj",
        "📊 Centralizator",
    ]
)


# ============================================================
# 1. LIVRATORI
# ============================================================

with tab_livr:
    st.subheader("🛵 Căutare & Gestionare Livratori")

    cautare = st.text_input(
        "🔎 Introdu numele livratorului pentru căutare:"
    )

    livratori = cauta_livratori(cautare)

    if cautare.strip() and not livratori:
        st.warning(
            f"Livratorul **'{cautare.strip()}'** nu există în listă."
        )

        if st.button(
            f"➕ Adaugă-l pe '{cautare.strip()}' în baza de date"
        ):
            ok, mesaj = adauga_livrator(cautare)
            if ok:
                st.success(mesaj)
                st.rerun()
            else:
                st.error(mesaj)

    elif livratori:
        st.write(f"Rezultate găsite: **{len(livratori)}**")

        for livrator in livratori:
            with st.container(border=True):
                c1, c2 = st.columns([0.8, 0.2])

                c1.markdown(
                    f"**{livrator['nume'].upper()}**"
                )

                if c2.button(
                    "Șterge",
                    key=f"delete_livrator_{livrator['id']}",
                ):
                    sterge_livrator(livrator["id"])
                    st.success("Livrator șters.")
                    st.rerun()
    else:
        st.info("Introdu un nume pentru a căuta un livrator.")


# ============================================================
# 2. DISPECERAT
# ============================================================

with tab_disp:
    s = get_session()

    col_st, col_ac = st.columns(2)

    start = col_st.number_input(
        "Start:",
        min_value=0,
        value=int(s["start_comenzi"]),
        step=1,
    )

    actual = col_ac.number_input(
        "Act:",
        min_value=0,
        value=int(s["actual_comenzi"]),
        step=1,
    )

    if actual < start:
        st.error(
            "Valoarea «Act» nu poate fi mai mică decât «Start»."
        )
    else:
        comenzi_curente = actual - start
        st.info(f"✅ **{comenzi_curente}** comenzi în total.")

    if (
        start != int(s["start_comenzi"])
        or actual != int(s["actual_comenzi"])
    ):
        save_session(
            start,
            actual,
            s["target"],
            s["tura_activa"],
        )

    c1, c2 = st.columns([0.4, 0.6])

    with c1:
        with st.expander("🧮 Calculator Discount", expanded=True):
            p = st.number_input(
                "Total (preț):",
                min_value=0.0,
                format="%.2f",
                key="calc_pret",
            )

            incasat = st.number_input(
                "Încasat:",
                min_value=0.0,
                format="%.2f",
                key="calc_incasat",
            )

            if st.button("Calculează Discount"):
                diferenta = p - incasat

                if diferenta < 0:
                    st.warning(
                        f"Încasarea depășește totalul cu "
                        f"{abs(diferenta):.2f} lei."
                    )
                else:
                    st.success(
                        f"Diferență: **{diferenta:.2f} lei**"
                    )

        if st.button(
            "💾 Salvează și Închide Tura",
            type="primary",
            use_container_width=True,
        ):
            if actual < start:
                st.error(
                    "Nu poți închide tura cât timp «Act» < «Start»."
                )
            else:
                finalizeaza_tura("manual")
                st.success(
                    "Tura a fost încheiată, salvată și raportată."
                )
                st.rerun()

    with c2:
        with st.expander(
            "🎯 Target (Scrie suma direct)",
            expanded=True,
        ):
            target = st.number_input(
                "Introdu valoarea targetului (lei):",
                min_value=0.0,
                value=float(s["target"]),
                step=1.0,
                format="%.2f",
            )

            if target != float(s["target"]):
                save_session(
                    s["start_comenzi"],
                    s["actual_comenzi"],
                    target,
                    s["tura_activa"],
                )

            st.write(f"### Target curent: {target:.2f} lei")

            if st.button("RESET TARGET"):
                save_session(
                    s["start_comenzi"],
                    s["actual_comenzi"],
                    0.0,
                    s["tura_activa"],
                )
                st.success("Targetul a fost resetat.")
                st.rerun()


# ============================================================
# 3. CALCULATOR PROCENT
# ============================================================

with tab_calc:
    st.subheader("🧮 Calculator Avansat de Procente")

    optiune = st.radio(
        "Ce vrei să calculezi?",
        [
            "1. Cât reprezintă X % dintr-o sumă?",
            "2. Ce procent reprezintă o parte dintr-un total?",
            "3. Aplică o creștere sau reducere procentuală",
        ],
    )

    st.divider()

    if optiune.startswith("1"):
        c1, c2 = st.columns(2)

        suma = c1.number_input(
            "Valoarea totală:",
            min_value=0.0,
            value=100.0,
            step=1.0,
        )

        procent = c2.number_input(
            "Procentul %:",
            min_value=0.0,
            value=10.0,
            step=0.5,
        )

        rezultat = suma * procent / 100

        st.success(
            f"**Rezultat:** {procent}% din {suma:.2f} = "
            f"**{rezultat:.2f}**"
        )

    elif optiune.startswith("2"):
        c1, c2 = st.columns(2)

        parte = c1.number_input(
            "Valoarea parțială:",
            min_value=0.0,
            value=20.0,
            step=1.0,
        )

        total = c2.number_input(
            "Valoarea totală:",
            min_value=0.0,
            value=100.0,
            step=1.0,
        )

        if total > 0:
            rezultat = parte / total * 100
            st.success(
                f"**Rezultat:** {parte:.2f} reprezintă "
                f"**{rezultat:.2f}%** din {total:.2f}"
            )
        else:
            st.error("Totalul trebuie să fie mai mare decât 0.")

    else:
        c1, c2, c3 = st.columns(3)

        baza = c1.number_input(
            "Suma inițială:",
            min_value=0.0,
            value=100.0,
            step=1.0,
        )

        procent = c2.number_input(
            "Procentul %:",
            min_value=0.0,
            value=10.0,
            step=0.5,
        )

        operatie = c3.selectbox(
            "Operație:",
            ["Creștere (+)", "Reducere (-)"],
        )

        diferenta = baza * procent / 100

        if operatie.startswith("Creștere"):
            rezultat = baza + diferenta
            st.success(
                f"Rezultat: **{rezultat:.2f}** "
                f"(+{diferenta:.2f})"
            )
        else:
            rezultat = baza - diferenta
            st.success(
                f"Rezultat: **{rezultat:.2f}** "
                f"(-{diferenta:.2f})"
            )


# ============================================================
# 4. PONTAJ
# ============================================================

with tab_pontaj:
    st.subheader("🕐 Sistem de Pontaj Operator")

    s = get_session()

    c1, c2 = st.columns(2)

    with c1:
        if st.button(
            "🟢 Începe Tura (Check-in)",
            use_container_width=True,
        ):
            if s["tura_activa"]:
                st.warning("Există deja o tură activă.")
            else:
                timp = now_local()

                save_session(
                    s["start_comenzi"],
                    s["actual_comenzi"],
                    s["target"],
                    timp.isoformat(timespec="seconds"),
                )

                trimite_pe_telegram(
                    "🟢 *Check-in efectuat*\n"
                    f"👤 Operator: {OPERATOR_NUME}\n"
                    f"🕐 Ora: `{fmt_time(timp)}`"
                )

                st.success(
                    f"Tura a început la {fmt_time(timp)}."
                )
                st.rerun()

    with c2:
        if st.button(
            "🔴 Încheie Tura (Check-out)",
            use_container_width=True,
        ):
            s = get_session()

            if not s["tura_activa"]:
                st.warning("Nu există nicio tură activă.")
            else:
                timp_inceput = parse_datetime(s["tura_activa"])
                timp_sfarsit = now_local()

                ore = round(
                    (
                        timp_sfarsit - timp_inceput
                    ).total_seconds() / 3600,
                    2,
                )

                adauga_pontaj(
                    OPERATOR_NUME,
                    fmt_date(timp_inceput),
                    fmt_time(timp_inceput),
                    fmt_time(timp_sfarsit),
                    ore,
                )

                trimite_pe_telegram(
                    "🔴 *Check-out efectuat*\n"
                    f"👤 Operator: {OPERATOR_NUME}\n"
                    f"🕐 Check-out: `{fmt_time(timp_sfarsit)}`\n"
                    f"⏱️ Total ore: *{ore}*"
                )

                save_session(
                    s["start_comenzi"],
                    s["actual_comenzi"],
                    0.0,
                    None,
                )

                st.success(
                    f"Tura a fost încheiată. "
                    f"Total ore: {ore}."
                )
                st.rerun()

    if s["tura_activa"]:
        timp_inceput = parse_datetime(s["tura_activa"])
        durata = now_local() - timp_inceput

        st.info(
            f"🟢 **Tură activă** — începută la "
            f"`{timp_inceput.strftime('%d.%m.%Y %H:%M:%S')}`. "
            f"Se închide automat după 12 ore."
        )

        st.metric(
            "Durată curentă",
            f"{durata.total_seconds() / 3600:.2f} ore",
        )

    st.divider()
    st.subheader("📋 Istoric Pontaj")

    pontaj = pontaj_dataframe()

    if not pontaj.empty:
        st.dataframe(
            pontaj,
            use_container_width=True,
            hide_index=True,
        )

        csv = pontaj.to_csv(index=False).encode("utf-8-sig")

        st.download_button(
            "📥 Descarcă pontaj CSV",
            data=csv,
            file_name="pontaj_presto.csv",
            mime="text/csv",
        )

        if st.button("🗑️ Șterge tot istoricul de pontaj"):
            sterge_istoric_pontaj()
            st.success("Istoricul a fost șters.")
            st.rerun()
    else:
        st.info("Nu există înregistrări în pontaj.")


# ============================================================
# 5. CENTRALIZATOR
# ============================================================

with tab_centr:
    st.subheader("📊 Analiză & Istoric Ture")

    with st.expander(
        "➕ Adaugă Manual un Raport în Centralizator",
        expanded=False,
    ):
        with st.form("formular_raport_manual"):
            data = st.date_input(
                "Data raportului:",
                value=now_local().date(),
            )

            comenzi = st.number_input(
                "Număr comenzi:",
                min_value=0,
                value=10,
                step=1,
            )

            target = st.number_input(
                "Valoare target (lei):",
                min_value=0.0,
                value=50.0,
                step=0.5,
                format="%.2f",
            )

            if st.form_submit_button(
                "💾 Salvează în Baza de Date"
            ):
                data_str = data.strftime("%d.%m.%Y")

                adauga_raport(
                    data_str,
                    comenzi,
                    target,
                )

                trimite_pe_telegram(
                    "📝 *Raport adăugat manual*\n"
                    f"📅 Data: {data_str}\n"
                    f"📦 Comenzi: {comenzi}\n"
                    f"🎯 Target: {target:.2f} lei"
                )

                st.success("Raportul a fost adăugat.")
                st.rerun()

    rapoarte = lista_rapoarte()

    total_comenzi = sum(
        int(r["comenzi"]) for r in rapoarte
    )

    total_target = sum(
        safe_float(r["target"]) for r in rapoarte
    )

    m1, m2, m3 = st.columns(3)

    m1.metric(
        "Total Comenzi",
        total_comenzi,
    )

    m2.metric(
        "Total Target",
        f"{total_target:.2f} lei",
    )

    m3.metric(
        "Ture/Rapoarte",
        len(rapoarte),
    )

    if rapoarte:
        df = rapoarte_dataframe()

        st.divider()

        if st.button(
            "📤 Trimite Centralizatorul pe Telegram",
            use_container_width=True,
        ):
            mesaj = (
                "📊 *CENTRALIZATOR COMENZI PRESTO*\n\n"
                f"📦 *Total Comenzi:* {total_comenzi}\n"
                f"🎯 *Total Target:* {total_target:.2f} lei\n\n"
                "📋 *Istoric Ture:*\n"
            )

            for r in reversed(rapoarte):
                mesaj += (
                    f"• {r['data_raport']} | "
                    f"{r['comenzi']} comenzi | "
                    f"{r['target']:.2f} lei\n"
                )

            if trimite_pe_telegram(mesaj):
                st.success("Centralizator trimis pe Telegram.")
            else:
                st.error("Trimiterea pe Telegram a eșuat.")

        st.subheader("📈 Evoluție Comenzi")

        df_grafic = (
            df.groupby("data_raport", as_index=False)["comenzi"]
            .sum()
        )

        st.bar_chart(
            df_grafic,
            x="data_raport",
            y="comenzi",
        )

        st.divider()
        st.subheader("📋 Istoric Detaliat")

        for raport in rapoarte:
            rid = raport["id"]

            with st.container(border=True):
                c_info, c_edit, c_del = st.columns(
                    [0.65, 0.175, 0.175]
                )

                c_info.write(
                    f"📄 **{raport['data_raport']}** | "
                    f"{raport['comenzi']} comenzi | "
                    f"{raport['target']:.2f} lei"
                )

                edit_key = f"edit_{rid}"

                if c_edit.button(
                    "✏️ Editează",
                    key=f"edit_btn_{rid}",
                ):
                    st.session_state[edit_key] = True

                if c_del.button(
                    "❌ Șterge",
                    key=f"del_btn_{rid}",
                ):
                    sterge_raport(rid)
                    st.success("Raport șters.")
                    st.rerun()

                if st.session_state.get(edit_key, False):
                    with st.form(
                        key=f"form_edit_{rid}"
                    ):
                        try:
                            data_obj = datetime.strptime(
                                raport["data_raport"],
                                "%d.%m.%Y",
                            ).date()
                        except ValueError:
                            data_obj = now_local().date()

                        data_noua = st.date_input(
                            "Data raportului:",
                            value=data_obj,
                        )

                        comenzi_noi = st.number_input(
                            "Comenzi:",
                            min_value=0,
                            value=int(raport["comenzi"]),
                            step=1,
                        )

                        target_nou = st.number_input(
                            "Target (lei):",
                            min_value=0.0,
                            value=float(raport["target"]),
                            format="%.2f",
                            step=0.1,
                        )

                        c_save, c_cancel = st.columns(2)

                        if c_save.form_submit_button(
                            "Salvează Modificările"
                        ):
                            actualizeaza_raport(
                                rid,
                                data_noua.strftime("%d.%m.%Y"),
                                comenzi_noi,
                                target_nou,
                            )

                            st.session_state[edit_key] = False
                            st.success("Raport modificat.")
                            st.rerun()

                        if c_cancel.form_submit_button(
                            "Anulează"
                        ):
                            st.session_state[edit_key] = False
                            st.rerun()

        st.divider()

        csv = df.to_csv(index=False).encode("utf-8-sig")

        st.download_button(
            "📥 Descarcă centralizator CSV",
            data=csv,
            file_name="centralizator_presto.csv",
            mime="text/csv",
        )

    else:
        st.info(
            "Nu există rapoarte salvate. "
            "Finalizează o tură sau adaugă un raport manual."
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()
st.caption(
    f"Asistent Presto • Operator: {OPERATOR_NUME} • "
    f"{now_local().strftime('%d.%m.%Y %H:%M:%S')}"
)
