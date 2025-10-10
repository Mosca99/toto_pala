import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

st.set_page_config(page_title="Classifica Giocatori", layout="wide")

# ------------------------------
# CONFIGURAZIONE
# ------------------------------
PASSWORD_ADMIN = "admin123"
GIOCATORI = [
    "Luca Inte",
    "Masi",
    "Mosca",
    "Rego",
    "Ripa",
    "Samu",
    "Ste",
    "Tony",
    "Vito"
]
NUM_GIORNATE = 30

GIOCATORI_CREDS = {
    "Luca Inte": "pass1",
    "Masi": "pass2",
    "Mosca": "pass3",
    "Rego": "pass4",
    "Ripa": "pass5",
    "Samu": "pass6",
    "Ste": "pass7",
    "Tony": "pass8",
    "Vito": "pass9"
}

# ------------------------------
# CONNESSIONE GOOGLE SHEETS
# ------------------------------
def connect_gs():
    creds_dict = json.loads(st.secrets["google_sheets"]["credentials"])
    scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(st.secrets["google_sheets"]["sheet_id"])
    return sheet

sheet = connect_gs()

# ------------------------------
# FUNZIONI DI LETTURA/SALVATAGGIO
# ------------------------------

def load_admin_df():
    try:
        ws = sheet.worksheet("Punteggi_Admin")
        data = ws.get_all_records()
        return pd.DataFrame(data)
    except:
        ws = sheet.add_worksheet(title="Punteggi_Admin", rows="100", cols="20")
        return pd.DataFrame(columns=["giornata","giocatore","punteggio"])

def save_admin_df(df):
    ws = sheet.worksheet("Punteggi_Admin")
    ws.clear()
    ws.update([df.columns.values.tolist()] + df.values.tolist())

def load_giocatori_df():
    try:
        ws = sheet.worksheet("Risultati_Giocatori")
        data = ws.get_all_records()
        return pd.DataFrame(data)
    except:
        ws = sheet.add_worksheet(title="Risultati_Giocatori", rows="500", cols="20")
        return pd.DataFrame(columns=["username","giornata"] + [f"partita{i+1}" for i in range(8)])

def save_giocatori_df(df):
    ws = sheet.worksheet("Risultati_Giocatori")
    ws.clear()
    ws.update([df.columns.values.tolist()] + df.values.tolist())

# ------------------------------
# MENU LATERALE
# ------------------------------
st.sidebar.title("🏆 Menu")
pagina = st.sidebar.radio(
    "Naviga tra le pagine:",
    ["Classifica Generale", "Classifiche per Giornata", "Area Admin", "Inserimento Giocatori"]
)

# ==============================
# CLASSIFICA GENERALE
# ==============================
if pagina == "Classifica Generale":
    st.title("🏆 Classifica Generale")
    df_admin = load_admin_df()
    def reset_da_giornata(df):
        giornate_reset = df[df["punteggio"] == 8]["giornata"]
        if not giornate_reset.empty:
            ultima_reset = giornate_reset.max()
            df = df[df["giornata"] > ultima_reset]
        return df
    def calcola_classifica(df):
        if df.empty:
            return pd.DataFrame(columns=["giocatore","punti_classifica","somma_punteggi"])
        df_valido = reset_da_giornata(df.copy())
        punti_classifica = {g:0 for g in GIOCATORI}
        somma_punteggi = {g:0 for g in GIOCATORI}
        for giornata, gruppo in df_valido.groupby("giornata"):
            max_p = gruppo["punteggio"].max()
            vincitori = gruppo[gruppo["punteggio"]==max_p]["giocatore"]
            for v in vincitori:
                punti_classifica[v] += 1
            for _, riga in gruppo.iterrows():
                somma_punteggi[riga["giocatore"]] += riga["punteggio"]
        classifica = pd.DataFrame({
            "giocatore": GIOCATORI,
            "punti_classifica":[punti_classifica[g] for g in GIOCATORI],
            "somma_punteggi":[somma_punteggi[g] for g in GIOCATORI]
        }).sort_values(by=["punti_classifica","somma_punteggi"], ascending=[False,False]).reset_index(drop=True)
        return classifica
    classifica = calcola_classifica(df_admin)
    st.dataframe(classifica, use_container_width=True)

# ==============================
# CLASSIFICHE PER GIORNATA
# ==============================
elif pagina == "Classifiche per Giornata":
    st.title("📅 Classifiche per Giornata")
    df_admin = load_admin_df()
    if df_admin.empty:
        st.info("Nessun punteggio inserito ancora.")
    else:
        if "giornata_sel" not in st.session_state:
            st.session_state.giornata_sel = int(df_admin["giornata"].min())
        col1,col2,col3 = st.columns([1,2,1])
        with col1:
            if st.button("⬅️ Giorno precedente"):
                st.session_state.giornata_sel = max(1, st.session_state.giornata_sel-1)
        with col3:
            if st.button("Giorno successivo ➡️"):
                st.session_state.giornata_sel = min(NUM_GIORNATE, st.session_state.giornata_sel+1)
        giornata_sel = st.session_state.giornata_sel
        st.subheader(f"Giornata {giornata_sel}")
        gior_df = df_admin[df_admin["giornata"]==giornata_sel].sort_values(by="punteggio",ascending=False)
        if gior_df.empty:
            st.warning("Nessun punteggio per questa giornata.")
        else:
            st.dataframe(gior_df,use_container_width=True)

# ==============================
# AREA ADMIN
# ==============================
elif pagina == "Area Admin":
    st.title("🔒 Area Admin")
    password = st.text_input("Inserisci la password:", type="password")
    if password == PASSWORD_ADMIN:
        st.success("Accesso consentito ✅")
        giornata = st.number_input("Giornata", min_value=1, max_value=NUM_GIORNATE, step=1)
        st.write("Inserisci i punteggi (0-8):")
        nuovi_punteggi = []
        cols = st.columns(2)
        for i,g in enumerate(GIOCATORI):
            with cols[i%2]:
                val = st.number_input(g, min_value=0, max_value=8, step=1, key=f"{giornata}_{g}")
                nuovi_punteggi.append({"giornata":giornata,"giocatore":g,"punteggio":val})
        if st.button("💾 Salva Punteggi"):
            df = load_admin_df()
            df = df[df["giornata"] != giornata]
            df = pd.concat([df, pd.DataFrame(nuovi_punteggi)], ignore_index=True)
            save_admin_df(df)
            st.success(f"Punteggi giornata {giornata} salvati correttamente!")
    elif password:
        st.error("Password errata ❌")

# ==============================
# INSERIMENTO GIOCATORI
# ==============================
elif pagina == "Inserimento Giocatori":
    st.title("📝 Inserimento Risultati Giocatori")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if username in GIOCATORI_CREDS and password == GIOCATORI_CREDS[username]:
        st.success(f"Accesso consentito: {username}")
        giornata = st.number_input("Seleziona giornata (6-30)", min_value=6, max_value=30, step=1)

        df_ris = st.session_state.risultati_giocatori
        st.subheader(f"Giornata {giornata}")
        risultati = []
        col1, col2 = st.columns(2)
        for i in range(8):
            with (col1 if i % 2 == 0 else col2):
                val = st.selectbox(f"Partita {i+1}", options=["1","X","2"], key=f"{username}_{giornata}_{i}")
                risultati.append(val)

        if st.button("💾 Salva Risultati"):
            df_ris = df_ris[~((df_ris["username"]==username) & (df_ris["giornata"]==giornata))]
            nuovo_record = {"username": username, "giornata": giornata}
            for i in range(8):
                nuovo_record[f"partita{i+1}"] = risultati[i]
            df_ris = pd.concat([df_ris, pd.DataFrame([nuovo_record])], ignore_index=True)
            st.session_state.risultati_giocatori = df_ris
            st.success("Risultati salvati correttamente ✅")

    elif username or password:
        st.error("Username o password errati ❌")
