import streamlit as st
import pandas as pd
import datetime as dt
import os
import json

st.set_page_config(layout="wide")

DATA_FILE = "data.csv"
CONFIG_FILE = "config.json"

# --- CHARGEMENT ROBUSTE ---
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        # Nettoyage immédiat des doublons
        df = df.drop_duplicates()
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        return df
    return pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note', 'Statut'])

def save_data(df):
    df = df.drop_duplicates()
    df.to_csv(DATA_FILE, index=False)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f: return json.load(f)
    return {'dossiers': {"PASS": []}, 'cadencier': [1, 3, 7, 14, 30], 'seuils': {'1': 12, '3': 12, '7': 14, '14': 14, '30': 16}}

# Initialisation
if 'data' not in st.session_state: st.session_state.data = load_data()
if 'config' not in st.session_state: st.session_state.config = load_config()

# --- SIDEBAR FIXE ---
st.sidebar.title("⚙️ Pilot Expert")
with st.sidebar.expander("🛠️ Réglages"):
    cad_input = st.text_input("Cadencier", ",".join(map(str, st.session_state.config['cadencier'])))
    st.session_state.config['cadencier'] = [int(x.strip()) for x in cad_input.split(",")]
    if st.button("💾 Enregistrer"): 
        with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)
        st.rerun()

# Gestion Dossiers/Matières séparée
dossier_nom = st.sidebar.text_input("Nouveau Dossier")
if st.sidebar.button("➕ Créer Dossier") and dossier_nom:
    st.session_state.config['dossiers'][dossier_nom] = []
    with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)
    st.rerun()

choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.config['dossiers'].keys()))

matiere_nom = st.sidebar.text_input("Ajouter Matière")
if st.sidebar.button("➕ Ajouter Matière") and matiere_nom:
    st.session_state.config['dossiers'][choix_dos].append(matiere_nom)
    with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)
    st.rerun()

page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie"])

# --- DASHBOARD (Purge réelle) ---
if page == "Dashboard":
    st.title(f"🎯 {choix_dos}")
    df = st.session_state.data
    df_dos = df[df['Dossier'] == choix_dos]
    
    st.subheader("⚠️ Rattrapages")
    rattrapages = df_dos[(df_dos['Note'] > 0) & (df_dos['Note'] < 12)]
    
    if not rattrapages.empty:
        st.table(rattrapages[['Matiere', 'Chapitre', 'J_Type', 'Note']])
        if st.button("🔄 Réintégrer (Purger l'ancien)"):
            for idx, row in rattrapages.iterrows():
                # Ajout nouvelle ligne
                new_r = row.copy()
                new_r['Date'] = dt.date.today()
                new_r['J_Type'] = 'RAT'
                new_r['Note'] = 0
                st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_r])])
                # Suppression définitive de l'ancienne
                st.session_state.data = st.session_state.data.drop(idx)
            save_data(st.session_state.data); st.rerun()

# --- PLANNING (Affichage propre) ---
elif page == "Planning & Saisie":
    st.markdown("### ✍️ Ajouter Chapitre")
    with st.form("add_chap"):
        mat = st.selectbox("Matière", st.session_state.config['dossiers'].get(choix_dos, []))
        chap = st.text_input("Titre du Chapitre")
        d0 = st.date_input("Date J0")
        if st.form_submit_button("Ajouter"):
            for j in [0] + st.session_state.config['cadencier']:
                new_row = {'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': f'J{j}', 
                           'Date': d0 + dt.timedelta(days=j), 'Note': 0, 'Statut': 'À faire'}
                st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])])
            save_data(st.session_state.data); st.rerun()

    # Affichage Planning
    cols = st.columns(7)
    for i, day in enumerate([dt.date.today() + dt.timedelta(days=x) for x in range(7)]):
        with cols[i]:
            st.markdown(f"**{day.strftime('%d/%m')}**")
            df_day = st.session_state.data[(st.session_state.data['Date'] == day) & (st.session_state.data['Dossier'] == choix_dos)]
            for idx, r in df_day.iterrows():
                with st.expander(f"{r['Matiere']} ({r['J_Type']})"):
                    st.write(f"📖 **{r['Chapitre']}**")
                    if st.button("✅ Fait", key=f"f_{idx}"):
                        st.session_state.data.at[idx, 'Statut'] = 'Fait'
                        save_data(st.session_state.data); st.rerun()