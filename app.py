mport streamlit as st
import pandas as pd
import datetime as dt
import os
import json

st.set_page_config(layout="wide")

DATA_FILE = "data.csv"
CONFIG_FILE = "config.json"

# --- CORE ---
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f: return json.load(f)
    return {'cours_max': 5, 'cadencier': [1, 3, 7, 14, 30], 'seuils': {'1': 12, '3': 12, '7': 14, '14': 14, '30': 16}, 'dossiers': {"PASS": []}}

def save_config(config):
    with open(CONFIG_FILE, "w") as f: json.dump(config, f)

def load_data():
    if os.path.exists(DATA_FILE):
        # Lecture forcée avec typage
        df = pd.read_csv(DATA_FILE)
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        return df.drop_duplicates()
    return pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note', 'Statut', 'Date_Examen'])

def save_data(df):
    # Nettoyage avant chaque écriture
    df = df.drop_duplicates()
    df.to_csv(DATA_FILE, index=False)

if 'config' not in st.session_state: st.session_state.config = load_config()
if 'data' not in st.session_state: st.session_state.data = load_data()

# --- SIDEBAR ---
st.sidebar.title("⚙️ Pilot Expert")
# Bouton de secours si le fichier est bloqué
if st.sidebar.button("⚠️ Réinitialiser DATA (si erreur)"):
    if os.path.exists(DATA_FILE): os.remove(DATA_FILE)
    st.session_state.data = load_data()
    st.rerun()

# ... (Le reste des réglages) ...
choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.config['dossiers'].keys()))

# --- DASHBOARD (Réintégration avec vérification) ---
if page == "Dashboard":
    # ... (code précédent)
    if st.button("🔄 Réintégrer Rattrapages", key="btn_reinteg"):
        rattrapages = st.session_state.data[(st.session_state.data['Dossier'] == choix_dos) & 
                                            (st.session_state.data['Note'] > 0) & 
                                            (st.session_state.data['Note'] < 12)]
        if not rattrapages.empty:
            for idx, row in rattrapages.iterrows():
                new_r = row.copy()
                new_r['Date'] = dt.date.today()
                new_r['J_Type'] = 'RAT'
                new_r['Statut'] = 'À faire'
                st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_r])], ignore_index=True)
                st.session_state.data.at[idx, 'Statut'] = 'Fait'
            save_data(st.session_state.data)
            st.rerun()
