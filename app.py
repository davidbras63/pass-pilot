 import streamlit as st
import pandas as pd
import json
import os

# --- FICHIERS ---
CONFIG_FILE = "config.json"
DATA_FILE = "data.csv"

# --- CHARGEMENT ---
def init_app():
    # 1. Config
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            st.session_state.config = json.load(f)
    else:
        st.session_state.config = {
            'cours_max': 5,
            'cadencier': [1, 3, 7, 14, 30],
            'seuils': {'1': 10, '3': 12, '7': 14, '14': 15, '30': 16},
            'dossiers': {"PASS": ["UE1", "UE2"]}
        }
    
    # 2. Data
    if os.path.exists(DATA_FILE):
        st.session_state.data = pd.read_csv(DATA_FILE)
    else:
        st.session_state.data = pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note'])

if 'config' not in st.session_state: init_app()

# --- SIDEBAR (Réglages avec disquette) ---
st.sidebar.title("⚙️ Pilot Expert")

with st.sidebar.expander("🛠️ Réglages", expanded=True):
    st.session_state.config['cours_max'] = st.number_input("Cours max/jour", 1, 20, st.session_state.config['cours_max'])
    
    cad_input = st.text_input("Cadencier", ",".join(map(str, st.session_state.config['cadencier'])))
    
    # Bouton de sauvegarde explicite
    if st.button("💾 Enregistrer réglages"):
        st.session_state.config['cadencier'] = [int(x.strip()) for x in cad_input.split(",")]
        with open(CONFIG_FILE, "w") as f:
            json.dump(st.session_state.config, f)
        st.success("Config sauvegardée !")
        st.rerun()

# --- LOGIQUE D'AFFICHAGE ---
# Ici tu places tout le reste de ton code (Dashboard, Planning, etc.)
# En utilisant st.session_state.config['cours_max'] par exemple pour tes calculs.

st.write("Réglages actuels chargés :", st.session_state.config)

