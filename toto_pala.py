import streamlit as st
import pandas as pd
import base64
import requests
from io import StringIO

# ------------------------------
# CONFIGURAZIONE BASE
# ------------------------------
st.set_page_config(page_title="Classifica Giocatori", layout="wide")

PASSWORD_ADMIN = "fantazzolo2025"
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
    r = requests.get(
        github_api(f"contents/{GITHUB_FILE}"),
        headers={"Authorization": f"token {GITHUB_TOKEN}"}
    )
    if r.status_code == 200:
        return r.json()["sha"]
    return None

def save_data(df):
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    b64_content = base64.b64encode(csv_bytes).decode("utf-8")
    sha = get_file_sha()
    data = {"message": "Aggiornamento punteggi da Streamlit", "content": b64_content, "branch": BRANCH}
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
    r = requests.get(
        github_api(f"contents/{GITHUB_FILE}"),
        headers={"Authorization": f"token {GITHUB_TOKEN}"}
    )
    if r.status_code == 200:
        content = base64.b64decode(r.json()["content"]).decode("utf-8")
        return pd.read_csv(StringIO(content))
    else:
        df = pd.DataFrame(columns=["giornata", "giocatore", "punteggio"])
        save_data(df)
        return df

# ------------------------------
# FUNZIONI DI CALCOLO
# ------------------------------
def calcola_classifica_generale(df):
    if df.empty:
        return pd.DataFrame(columns=["giocatore", "punti_classifica", "somma_punteggi"])
    
    punti_classifica = {g: 0 for g in GIOCATORI}
    somma_punteggi = {g: 0 for g in GIOCATORI}

    for giornata in sorted(df["giornata"].unique()):
        subset = df[df["giornata"] == giornata]
        if subset.empty:
            continue
        max_punteggio = subset["punteggio"].max()
        vincitori = subset[subset["punteggio"] == max_punteggio]["giocatore"].tolist()
        for g in vincitori:
            punti_classifica[g] += 1
        for g, p in zip(subset["giocatore"], subset["punteggio"]):
            somma_punteggi[g] += p

    classifica = pd.DataFrame({
        "giocatore": list(punti_classifica.keys()),
        "punti_classifica": list(punti_classifica.values()),
        "somma_punteggi": list(somma_punteggi.values())
    })
    classifica = classifica.sort_values(["punti_classifica", "somma_punteggi"], ascending=[False, False])
    return classifica

# ------------------------------
# MENU LATERALE
# ------------------------------
st.sidebar.title("Menu")
pagina = st.sidebar.radio("Seleziona pagina", ["Classifica Generale", "Classifica per Giornata", "Admin"])

df = load_data()

# ------------------------------
# PAGINA 1: CLASSIFICA GENERALE
# ------------------------------
if pagina == "Classifica Generale":
    st.title("📊 Classifica Generale")
    classifica = calcola_classifica_generale(df)
    st.dataframe(classifica, use_container_width=True)

# ------------------------------
# PAGINA 2: CLASSIFICA PER GIORNATA
# ------------------------------
elif pagina == "Classifica per Giornata":
    st.title("📅 Classifica per Giornata")
    giornata = st.selectbox("Seleziona Giornata", sorted(df["giornata"].unique()) if not df.empty else range(1, NUM_GIORNATE+1))
    subset = df[df["giornata"] == giornata]
    if subset.empty:
        st.warning(f"Nessun punteggio inserito per la giornata {giornata}")
    else:
        st.dataframe(subset.sort_values("punteggio", ascending=False), use_container_width=True)

# ------------------------------
# PAGINA 3: ADMIN
# ------------------------------
elif pagina == "Admin":
    st.title("🔑 Area Admin")
    password = st.text_input("Password Admin", type="password")
    if password != PASSWORD_ADMIN:
        st.warning("Accesso negato. Inserisci la password corretta.")
    else:
        st.success("Accesso Admin riuscito ✅")
        giornata = st.number_input("Giornata", min_value=1, max_value=NUM_GIORNATE, step=1)
        giocatore = st.selectbox("Giocatore", GIOCATORI)
        punteggio = st.number_input("Punteggio", min_value=0, max_value=10, step=1)

        if st.button("Salva Punteggio"):
            nuovo = pd.DataFrame([{"giornata": giornata, "giocatore": giocatore, "punteggio": punteggio}])
            df = pd.concat([df, nuovo], ignore_index=True)
            save_data(df)
            st.success(f"Punteggio salvato per {giocatore} (giornata {giornata}) ✅")

        if st.button("Reset Tutti i Dati"):
            df = pd.DataFrame(columns=["giornata", "giocatore", "punteggio"])
            save_data(df)
            st.warning("Tutti i dati sono stati resettati ⚠️")
