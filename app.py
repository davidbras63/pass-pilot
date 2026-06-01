import streamlit as st
import pandas as pd
import datetime as dt
import os
import json

st.set_page_config(layout="wide")

DATA_FILE = "data.csv"
CONFIG_FILE = "config.json"

# --- CHARGEMENT & SAUVEGARDE CONFIG ---
def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f: return json.load(f)
        except: pass
    return {'cours_max': 5, 'cadencier': [1, 3, 7, 14, 30], 'dossiers': {"PASS": []}}

# --- CHARGEMENT DONNÉES ---
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        return df.drop_duplicates()
    return pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note'])

def save_data(df):
    df.drop_duplicates(inplace=True)
    df.to_csv(DATA_FILE, index=False)

if 'config' not in st.session_state: st.session_state.config = load_config()
if 'data' not in st.session_state: st.session_state.data = load_data()

# --- SIDEBAR ---
st.sidebar.title("⚙️ Pilot Expert")
# Création dossier
nom_dossier = st.sidebar.text_input("Nouveau Dossier")
if st.sidebar.button("➕ Créer Dossier"):
    if nom_dossier and nom_dossier not in st.session_state.config['dossiers']:
        st.session_state.config['dossiers'][nom_dossier] = []
        save_config(st.session_state.config)
        st.rerun()

choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.config['dossiers'].keys()))

# Ajout Matière
nom_matiere = st.sidebar.text_input("Nom Matière")
if st.sidebar.button("➕ Ajouter Matière"):
    if nom_matiere and nom_matiere not in st.session_state.config['dossiers'][choix_dos]:
        st.session_state.config['dossiers'][choix_dos].append(nom_matiere)
        save_config(st.session_state.config)
        st.rerun()

page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie"])

# --- DASHBOARD ---
if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    st.subheader("📚 Matières")
    for m in st.session_state.config['dossiers'].get(choix_dos, []):
        c1, c2 = st.columns([4, 1])
        c1.info(f"📚 {m}")
        if c2.button("🗑️", key=f"del_{m}"):
            st.session_state.config['dossiers'][choix_dos].remove(m)
            save_config(st.session_state.config)
            st.rerun()