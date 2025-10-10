import streamlit as st
import pandas as pd
import os

# ------------------------------
# CONFIGURAZIONE BASE
# ------------------------------
st.set_page_config(page_title="Classifica Giocatori", layout="wide")

PASSWORD_ADMIN = "fantazzolo2025"  # <-- Cambia qui la tua password
DATA_FILE = "punteggi.csv"

GIOCATORI = [
    "Luca Inte",
    "Masi",
    "Mosca",
    "Rego",
    "Ripa",
    "Samu",
    "Spaglia",
    "Ste",
    "Tony",
    "Vito"
]
NUM_GIORNATE = 30

# ------------------------------
# FUNZIONI DI SUPPORTO
# ------------------------------

def init_data():
    """Crea o carica il file dati."""
    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame(columns=["giornata", "giocatore", "punteggio"])
        df.to_csv(DATA_FILE, index=False)
    else:
        df = pd.read_csv(DATA_FILE)
    return df

def salva_dati(df):
    df.to_csv(DATA_FILE, index=False)

def reset_da_giornata(df):
    """Se qualcuno ha preso 8, azzera la classifica da quella giornata in poi."""
    giornate_reset = df[df["punteggio"] == 8]["giornata"]
    if not giornate_reset.empty:
        ultima_reset = giornate_reset.max()
        df = df[df["giornata"] > ultima_reset]
    return df

def calcola_classifica(df):
    """Calcola la classifica generale secondo le regole."""
    if df.empty:
        return pd.DataFrame(columns=["giocatore", "punti_classifica", "somma_punteggi"])
    
    df_valido = reset_da_giornata(df.copy())

    punti_classifica = {g: 0 for g in GIOCATORI}
    somma_punteggi = {g: 0 for g in GIOCATORI}

    for giornata, gruppo in df_valido.groupby("giornata"):
        max_p = gruppo["punteggio"].max()
        vincitori = gruppo[gruppo["punteggio"] == max_p]["giocatore"]
        for v in vincitori:
            punti_classifica[v] += 1
        for _, riga in gruppo.iterrows():
            somma_punteggi[riga["giocatore"]] += riga["punteggio"]

    classifica = pd.DataFrame({
        "giocatore": GIOCATORI,
        "punti_classifica": [punti_classifica[g] for g in GIOCATORI],
        "somma_punteggi": [somma_punteggi[g] for g in GIOCATORI]
    }).sort_values(
        by=["punti_classifica", "somma_punteggi"], ascending=[False, False]
    ).reset_index(drop=True)

    return classifica

def calcola_classifica_giornata(df, giornata):
    """Restituisce la classifica di una giornata specifica."""
    gior = df[df["giornata"] == giornata]
    if gior.empty:
        return pd.DataFrame(columns=["giocatore", "punteggio"])
    return gior.sort_values(by="punteggio", ascending=False)

# ------------------------------
# INTERFACCIA STREAMLIT
# ------------------------------

st.sidebar.title("🏆 Menu")
pagina = st.sidebar.radio(
    "Naviga tra le pagine:",
    ["Classifica Generale", "Classifiche per Giornata", "Area Admin"]
)

df = init_data()

# ==============================
# PAGINA 1 - CLASSIFICA GENERALE
# ==============================
if pagina == "Classifica Generale":
    st.title("🏆 Classifica Generale")
    classifica = calcola_classifica(df)
    st.dataframe(classifica, use_container_width=True)

# ==============================
# PAGINA 2 - CLASSIFICHE PER GIORNATA
# ==============================
elif pagina == "Classifiche per Giornata":
    st.title("📅 Classifiche per Giornata")

    if df.empty:
        st.info("Nessun punteggio inserito ancora.")
    else:
        # Manteniamo lo stato della giornata selezionata
        if "giornata_sel" not in st.session_state:
            st.session_state["giornata_sel"] = int(df["giornata"].min())

        col1, col2, col3 = st.columns([1,2,1])
        with col1:
            if st.button("⬅️ Giorno precedente", use_container_width=True):
                st.session_state["giornata_sel"] = max(1, st.session_state["giornata_sel"] - 1)
        with col3:
            if st.button("Giorno successivo ➡️", use_container_width=True):
                st.session_state["giornata_sel"] = min(NUM_GIORNATE, st.session_state["giornata_sel"] + 1)

        giornata_sel = st.session_state["giornata_sel"]
        st.subheader(f"Giornata {giornata_sel}")

        gior_df = calcola_classifica_giornata(df, giornata_sel)
        if gior_df.empty:
            st.warning("Nessun punteggio per questa giornata.")
        else:
            st.dataframe(gior_df, use_container_width=True)

# ==============================
# PAGINA 3 - AREA ADMIN
# ==============================
elif pagina == "Area Admin":
    st.title("🔒 Area Amministratore")

    password = st.text_input("Inserisci la password:", type="password")
    if password == PASSWORD_ADMIN:
        st.success("Accesso consentito ✅")

        giornata = st.number_input("Giornata", min_value=1, max_value=NUM_GIORNATE, step=1)
        st.write("Inserisci i punteggi (da 0 a 8):")

        nuovi_punteggi = []
        cols = st.columns(2)
        for i, g in enumerate(GIOCATORI):
            with cols[i % 2]:
                val = st.number_input(g, min_value=0, max_value=8, step=1, key=f"{giornata}_{g}")
                nuovi_punteggi.append({"giornata": giornata, "giocatore": g, "punteggio": val})

        if st.button("💾 Salva Punteggi"):
            df = df[~(df["giornata"] == giornata)]  # rimuove eventuali record precedenti della giornata
            df = pd.concat([df, pd.DataFrame(nuovi_punteggi)], ignore_index=True)
            salva_dati(df)
            st.success(f"Punteggi della giornata {giornata} salvati correttamente!")

    elif password != "":
        st.error("Password errata ❌")

