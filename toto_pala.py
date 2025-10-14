import streamlit as st
import pandas as pd
import os
import base64
import requests

# ------------------------------
# CONFIGURAZIONE BASE
# ------------------------------
st.set_page_config(page_title="Classifica Giocatori", layout="wide")

PASSWORD_ADMIN = "fantazzolo2025"  # <-- cambia qui la password admin
NUM_GIORNATE = 30

GIOCATORI = [
    "Luca Inte", "Masi", "Mosca", "Rego", "Ripa",
    "Samu", "Spaglia", "Ste", "Tony", "Vito"
]

# ------------------------------
# CONFIGURAZIONE GITHUB
# ------------------------------
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
GITHUB_REPO = st.secrets["GITHUB_REPO"]
GITHUB_FILE = st.secrets["GITHUB_FILE"]
BRANCH = "main"

def github_api(url):
    return f"https://api.github.com/repos/{GITHUB_REPO}/{url}"

def get_file_sha():
    """Recupera lo SHA del file su GitHub (serve per aggiornare)."""
    r = requests.get(
        github_api(f"contents/{GITHUB_FILE}"),
        headers={"Authorization": f"token {GITHUB_TOKEN}"}
    )
    if r.status_code == 200:
        return r.json()["sha"]
    return None

def save_data(df):
    """Scrive il CSV aggiornato su GitHub."""
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    b64_content = base64.b64encode(csv_bytes).decode("utf-8")
    sha = get_file_sha()
    message = "Aggiornamento punteggi da Streamlit"

    data = {
        "message": message,
        "content": b64_content,
        "branch": BRANCH,
    }
    if sha:
        data["sha"] = sha

    r = requests.put(
        github_api(f"contents/{GITHUB_FILE}"),
        headers={"Authorization": f"token {GITHUB_TOKEN}"},
        json=data,
    )
    if r.status_code not in [200, 201]:
        st.error(f"Errore durante il salvataggio su GitHub: {r.text}")

def load_data():
    """Legge il CSV da GitHub o lo crea se non esiste."""
    r = requests.get(
        github_api(f"contents/{GITHUB_FILE}"),
        headers={"Authorization": f"token {GITHUB_TOKEN}"}
    )

    if r.status_code == 200:
        content = base64.b64decode(r.json()["content"]).decode("utf-8")
        return pd.read_csv(pd.compat.StringIO(content))
    else:
        df = pd.DataFrame(columns=["giornata", "giocatore", "punteggio"])
        save_data(df)
        return df

# ------------------------------
# FUNZIONI DI SUPPORTO
# ------------------------------
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

    for giornata in sorted(df_valido["giornata"].unique()):
        subset = df_valido[df_valido["giornata"] == giornata]
        if subset.empty:
            continue

        subset = subset.sort_values("punteggio", ascending=True)
        for idx, (giocatore, punteggio) in enumerate(zip(subset["giocatore"], subset["punteggio"])):
            punti = len(GIOCATORI) - idx
            punti_classifica[giocatore] += punti
            somma_punteggi[giocatore] += punteggio

    classifica = pd.DataFrame({
        "giocatore": list(punti_classifica.keys()),
        "punti_classifica": list(punti_classifica.values()),
        "somma_punteggi": list(somma_punteggi.values())
    })
    classifica = classifica.sort_values(["punti_classifica", "somma_punteggi"], ascending=[False, True])
    return classifica

# ------------------------------
# INTERFACCIA UTENTE
# ------------------------------
st.title("⚽ Classifica Giocatori")

df = load_data()

# --- Modalità admin ---
st.sidebar.header("Area Admin")
password = st.sidebar.text_input("Password Admin", type="password")

if password == PASSWORD_ADMIN:
    st.sidebar.success("Accesso Admin riuscito ✅")

    giornata = st.sidebar.number_input("Giornata", min_value=1, max_value=NUM_GIORNATE, step=1)
    giocatore = st.sidebar.selectbox("Giocatore", GIOCATORI)
    punteggio = st.sidebar.number_input("Punteggio", min_value=0, max_value=10, step=1)

    if st.sidebar.button("Salva Punteggio"):
        nuovo = pd.DataFrame([{"giornata": giornata, "giocatore": giocatore, "punteggio": punteggio}])
        df = pd.concat([df, nuovo], ignore_index=True)
        save_data(df)
        st.sidebar.success(f"Punteggio salvato per {giocatore} (giornata {giornata}) ✅")

    if st.sidebar.button("Reset Tutti i Dati"):
        df = pd.DataFrame(columns=["giornata", "giocatore", "punteggio"])
        save_data(df)
        st.sidebar.warning("Tutti i dati sono stati resettati ⚠️")

else:
    st.sidebar.warning("Inserisci la password admin per modificare i dati")

# --- Mostra la classifica ---
st.subheader("📊 Classifica Attuale")
classifica = calcola_classifica(df)
st.dataframe(classifica, use_container_width=True)

# --- Mostra i dati grezzi ---
with st.expander("Mostra dati grezzi"):
    st.dataframe(df, use_container_width=True)
