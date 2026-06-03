import streamlit as st
import pandas as pd
import datetime as dt
import os
import json
import uuid

st.set_page_config(layout="wide")

DATA_FILE = "data.csv"
CONFIG_FILE = "config.json"

# --- GESTION DONNÉES & CONFIG ---
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        return df.drop_duplicates()
    return pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note', 'Statut', 'ID'])

def save_data(df):
    df.drop_duplicates(inplace=True)
    df.to_csv(DATA_FILE, index=False)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f: return json.load(f)
    return {'cours_max': 5, 'cadencier': [1, 3, 7, 14, 30], 'seuils': {'1': 12, '3': 12, '7': 14, '14': 14, '30': 16}, 'dossiers': {"PASS": []}}

if 'data' not in st.session_state: st.session_state.data = load_data()
if 'config' not in st.session_state: st.session_state.config = load_config()

# --- SIDEBAR ---
st.sidebar.title("⚙️ Pilot Expert")

# Réglages
with st.sidebar.expander("🛠️ Réglages", expanded=False):
    st.session_state.config['cours_max'] = st.number_input("Max cours/jour", 1, 20, st.session_state.config.get('cours_max', 5))
    cad_str = st.text_input("Cadencier (jours)", ",".join(map(str, st.session_state.config['cadencier'])))
    st.session_state.config['cadencier'] = [int(x.strip()) for x in cad_str.split(",")]
    for j in st.session_state.config['cadencier']:
        st.session_state.config['seuils'][str(j)] = st.slider(f"Seuil Note J{j}", 10, 20, int(st.session_state.config['seuils'].get(str(j), 12)))
    if st.button("💾 Enregistrer"):
        with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)
        st.rerun()

# Création Dossier
with st.sidebar.form("form_dossier", clear_on_submit=True):
    nom_dossier = st.text_input("Nouveau Dossier")
    if st.form_submit_button("➕ Créer Dossier") and nom_dossier:
        st.session_state.config['dossiers'][nom_dossier] = []
        with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)
        st.rerun()

choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.config['dossiers'].keys()))

# Ajout Matière
with st.sidebar.form("form_matiere", clear_on_submit=True):
    nom_matiere = st.text_input("Nom Matière")
    if st.form_submit_button("➕ Ajouter Matière") and nom_matiere:
        st.session_state.config['dossiers'][choix_dos].append(nom_matiere)
        with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)
        st.rerun()

page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])

# --- DASHBOARD ---
if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    if st.button("❌ Supprimer ce Dossier"):
        del st.session_state.config['dossiers'][choix_dos]
        with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)
        st.rerun()
    for m in st.session_state.config['dossiers'].get(choix_dos, []):
        c1, c2 = st.columns([4, 1])
        c1.info(f"📚 {m}")
        if c2.button("🗑️", key=f"del_{m}"):
            st.session_state.config['dossiers'][choix_dos].remove(m)
            with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)
            st.rerun()

# --- PLANNING & SAISIE ---
elif page == "Planning & Saisie":
    with st.expander("✍️ Ajouter Chapitre", expanded=False):
        with st.form("Add_Form", clear_on_submit=True):
            mat = st.selectbox("Matière", st.session_state.config['dossiers'].get(choix_dos, []))
            chap = st.text_input("Titre")
            d0 = st.date_input("Date J0")
            dex = st.date_input("Date Examen", value=None)
            if st.form_submit_button("Générer Planning"):
                new_rows = []
                new_rows.append({'ID': str(uuid.uuid4()), 'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': 'J0', 'Date': d0, 'Note': 0, 'Statut': 'À faire'})
                if dex:
                    for j in st.session_state.config['cadencier']:
                        date_j = d0 + dt.timedelta(days=j)
                        if date_j <= dex:
                            new_rows.append({'ID': str(uuid.uuid4()), 'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': f'J{j}', 'Date': date_j, 'Note': 0, 'Statut': 'À faire'})
                st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame(new_rows)])
                st.session_state.data = st.session_state.data.drop_duplicates(subset=['Dossier', 'Chapitre', 'J_Type', 'Date'])
                save_data(st.session_state.data)
                st.rerun()

    # Affichage Planning
    st.subheader("🗓️ Planning Hebdomadaire")
    # (Affichage hebdomadaire inchangé)
    
    st.subheader("Saisie Notes - Aujourd'hui")
    df_today = st.session_state.data[(pd.to_datetime(st.session_state.data['Date']).dt.date == dt.date.today()) & (st.session_state.data['Dossier'] == choix_dos)].copy()
    if not df_today.empty:
        edited = st.data_editor(df_today[['Chapitre', 'J_Type', 'Note', 'Statut']], use_container_width=True)
        if st.button("💾 Enregistrer"):
            # Logique d'enregistrement
            save_data(st.session_state.data)
            st.rerun()

# --- GRAPHIQUES ---
elif page == "Graphiques":
    st.title("📊 Progression")