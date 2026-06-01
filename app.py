import streamlit as st
import pandas as pd
import datetime as dt
import os
import json

st.set_page_config(layout="wide")

DATA_FILE = "data.csv"
CONFIG_FILE = "config.json"

# --- CHARGEMENT ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce').dt.date
            df['Note'] = pd.to_numeric(df['Note'], errors='coerce').fillna(0)
            if 'Statut' not in df.columns: df['Statut'] = 'À faire'
            # Nettoyage des doublons stricts au chargement
            df = df.drop_duplicates(subset=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date'], keep='first')
            return df
        except: return pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note', 'Statut'])
    return pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note', 'Statut'])

def save_data(df): df.to_csv(DATA_FILE, index=False)

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f: return json.load(f)
        except: pass
    return {'cours_max': 5, 'cadencier': [1, 3, 7, 14, 30, 60, 90, 120], 
            'seuils': {'1': 12, '3': 12, '7': 14, '14': 14, '30': 16, '60': 16, '90': 18, '120': 18},
            'dossiers': {"PASS": []}}

if 'data' not in st.session_state: st.session_state.data = load_data()
if 'config' not in st.session_state: st.session_state.config = load_config()

# --- SIDEBAR ---
st.sidebar.title("⚙️ Pilot Expert")
with st.sidebar.expander("🛠️ Réglages", expanded=True):
    st.session_state.config['cours_max'] = st.number_input("Max cours/jour", 1, 20, st.session_state.config.get('cours_max', 5))
    cad_val = ",".join(map(str, st.session_state.config.get('cadencier', [1, 3, 7])))
    cad_input = st.text_input("Cadencier (jours)", cad_val)
    st.session_state.config['cadencier'] = [int(x.strip()) for x in cad_input.split(",")]
    for j in st.session_state.config['cadencier']:
        st.session_state.config['seuils'][str(j)] = st.slider(f"Seuil Note J{j}", 10, 20, int(st.session_state.config['seuils'].get(str(j), 12)))
    if st.button("💾 Enregistrer"): 
        with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)
        st.rerun()

choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.config['dossiers'].keys()))
if st.sidebar.button("➕ Créer Dossier"): 
    nom = st.sidebar.text_input("Nom nouveau dossier")
    if nom: st.session_state.config['dossiers'][nom] = []; st.rerun()
if st.sidebar.button("➕ Ajouter Matière"): 
    mat = st.sidebar.text_input("Nom Matière")
    if mat: st.session_state.config['dossiers'][choix_dos].append(mat); st.rerun()

page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])

# --- DASHBOARD ---
if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    for m in st.session_state.config['dossiers'].get(choix_dos, []):
        c1, c2 = st.columns([4, 1])
        c1.info(f"📚 {m}")
        if c2.button("🗑️", key=f"del_{m}"): st.session_state.config['dossiers'][choix_dos].remove(m); st.rerun()
    
    st.subheader("⚠️ Rattrapages")
    st.session_state.data['Note'] = pd.to_numeric(st.session_state.data['Note'], errors='coerce').fillna(0)
    df_filtered = st.session_state.data[st.session_state.data['Dossier'] == choix_dos]
    
    rattrapages = []
    for j in st.session_state.config['cadencier']:
        seuil = float(st.session_state.config['seuils'].get(str(j), 12))
        mask = (df_filtered['J_Type'] == f"J{j}") & (df_filtered['Note'] > 0) & (df_filtered['Note'] < seuil)
        rattrapages.append(df_filtered[mask])
    
    final = pd.concat(rattrapages) if rattrapages else pd.DataFrame()
    if not final.empty:
        disp = final.copy()
        disp['Date'] = disp['Date'].apply(lambda x: x.strftime('%d/%m/%Y'))
        st.table(disp[['Matiere', 'Chapitre', 'J_Type', 'Date', 'Note']])
        if st.button("🔄 Réintégrer Rattrapages"):
            for idx, row