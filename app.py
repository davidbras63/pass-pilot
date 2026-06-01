import streamlit as st
import pandas as pd
import datetime as dt
import os
import json

st.set_page_config(layout="wide")

# --- FICHIERS ---
DATA_FILE = "data.csv"
CONFIG_FILE = "config.json"

# --- CHARGEMENT ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce').dt.date
            return df
        except: pass
    return pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note'])

def save_data(df): df.to_csv(DATA_FILE, index=False)

def load_config():
    default = {
        'cours_max': 5, 
        'cadencier': [1, 3, 7, 14, 30, 60, 90, 120], 
        'seuils': {'1': 12, '3': 12, '7': 14, '14': 14, '30': 16, '60': 16, '90': 18, '120': 18},
        'dossiers': {"PASS": ["UE1", "UE2"]}
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f: 
                cfg = json.load(f)
                # Vérifie que toutes les clés existent, sinon remplit avec les défauts
                if 'dossiers' not in cfg: cfg['dossiers'] = default['dossiers']
                if 'config' not in cfg: cfg.update(default)
                return cfg
        except: return default
    return default

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f: json.dump(cfg, f)

# Initialisation session
if 'data' not in st.session_state: st.session_state.data = load_data()
if 'config' not in st.session_state: st.session_state.config = load_config()

# --- SIDEBAR ---
st.sidebar.title("⚙️ Pilot Expert")

with st.sidebar.expander("🛠️ Réglages", expanded=True):
    st.session_state.config['cours_max'] = st.number_input("Max cours/jour", 1, 20, st.session_state.config['cours_max'])
    cad_str = ",".join(map(str, st.session_state.config['cadencier']))
    cad_input = st.text_input("Cadencier", cad_str)
    st.session_state.config['cadencier'] = [int(x.strip()) for x in cad_input.split(",")]
    
    st.write("---")
    st.subheader("Seuils de notes par J")
    for j in st.session_state.config['cadencier']:
        val = st.slider(f"Seuil note J{j}", 10, 20, int(st.session_state.config['seuils'].get(str(j), 12)))
        st.session_state.config['seuils'][str(j)] = val
    
    if st.button("💾 Enregistrer Réglages"):
        save_config(st.session_state.config)
        st.success("Config sauvée !")
        st.rerun()

# --- GESTION DOSSIERS ---
dossiers = st.session_state.config.get('dossiers', {"PASS": ["UE1", "UE2"]})
new_folder = st.sidebar.text_input("Nouveau Dossier")
if st.sidebar.button("➕ Créer Dossier") and new_folder:
    st.session_state.config['dossiers'][new_folder] = []
    save_config(st.session_state.config); st.rerun()

choix_dos = st.sidebar.selectbox("Dossier", list(dossiers.keys()))

new_mat = st.sidebar.text_input("Ajouter Matière")
if st.sidebar.button("Ajouter Matière") and new_mat: 
    st.session_state.config['dossiers'][choix_dos].append(new_mat)
    save_config(st.session_state.config); st.rerun()

# --- NAVIGATION ---
page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])
df = st.session_state.data[st.session_state.data['Dossier'] == choix_dos].copy()

# --- PAGES ---
if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    for m in st.session_state.config['dossiers'].get(choix_dos, []):
        col1, col2 = st.columns([4, 1])
        col1.info(f"📚 {m}")
        if col2.button("🗑️", key=f"del_{m}"): 
            st.session_state.config['dossiers'][choix_dos].remove(m)
            save_config(st.session_state.config); st.rerun()
    st.table(df[df['Note'] != '0'])
    if st.button("🚀 Générer saisie"): save_data(st.session_state.data); st.rerun()

elif page == "Planning & Saisie":
    st.title("🗓️ Planning & Saisie")
    with st.form("Add"):
        c1, c2 = st.columns(2)
        mat = c1.selectbox("Matière", st.session_state.config['dossiers'].get(choix_dos, []))
        chap = c1.text_input("Nom")
        d0 = c2.date_input("Date J0", format="DD/MM/YYYY")
        if st.form_submit_button("Générer"):
            for j in [0] + st.session_state.config['cadencier']:
                d = d0 + dt.timedelta(days=j)
                if d.weekday() != 6:
                    new_row = {'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': f"J{j}", 'Date': d, 'Note': '0'}
                    st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=True)
            save_data(st.session_state.data); st.rerun()
    
    st.subheader("📝 Saisie des Notes")
    edited = st.data_editor(df, use_container_width=True)
    if st.button("Enregistrer"):
        st.session_state.data.update(edited)
        save_data(st.session_state.data); st.rerun()