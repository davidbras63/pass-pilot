import streamlit as st
import pandas as pd
import datetime as dt
import os
import json
import uuid

st.set_page_config(layout="wide")

DATA_FILE = "data.csv"
CONFIG_FILE = "config.json"

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
    return {'dossiers': {"PASS": []}}

if 'data' not in st.session_state: st.session_state.data = load_data()
if 'config' not in st.session_state: st.session_state.config = load_config()

# --- SIDEBAR ---
st.sidebar.title("⚙️ Pilot Expert")

# Gestion Dossiers
new_dossier = st.sidebar.text_input("Nouveau Dossier", value="", key="dossier_in")
if st.sidebar.button("➕ Créer Dossier") and new_dossier:
    st.session_state.config['dossiers'][new_dossier] = []
    with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)
    st.rerun()

choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.config['dossiers'].keys()))

# Gestion Matières
new_matiere = st.sidebar.text_input("Nom Matière", value="", key="matiere_in")
if st.sidebar.button("➕ Ajouter Matière") and new_matiere:
    st.session_state.config['dossiers'][choix_dos].append(new_matiere)
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
        st.info(f"📚 {m}")

# --- PLANNING & SAISIE ---
elif page == "Planning & Saisie":
    with st.expander("✍️ Ajouter Chapitre", expanded=True):
        with st.form("Add_Form", clear_on_submit=True):
            mat = st.selectbox("Matière", st.session_state.config['dossiers'].get(choix_dos, []))
            chap = st.text_input("Titre")
            d0 = st.date_input("Date J0")
            dex = st.date_input("Date Examen", value=None)
            if st.form_submit_button("Générer Planning"):
                if chap and dex:
                    new_rows = []
                    new_rows.append({'ID': str(uuid.uuid4()), 'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': 'J0', 'Date': d0, 'Note': 0, 'Statut': 'À faire'})
                    for j in [1, 3, 7, 14, 30]:
                        d_j = d0 + dt.timedelta(days=j)
                        if d_j <= dex:
                            new_rows.append({'ID': str(uuid.uuid4()), 'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': f'J{j}', 'Date': d_j, 'Note': 0, 'Statut': 'À faire'})
                    
                    st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame(new_rows)])
                    st.session_state.data = st.session_state.data.drop_duplicates(subset=['Dossier', 'Chapitre', 'J_Type', 'Date'])
                    save_data(st.session_state.data)
                    st.rerun()

    st.subheader("🗓️ Planning Hebdomadaire")
    cols = st.columns(7)
    today = dt.date.today()
    start = today - dt.timedelta(days=today.weekday())
    for i, col in enumerate(cols):
        day = start + dt.timedelta(days=i)
        with col:
            st.markdown(f"**{day.strftime('%d/%m')}**")
            temp = st.session_state.data[(pd.to_datetime(st.session_state.data['Date']).dt.date == day) & (st.session_state.data['Dossier'] == choix_dos)]
            for _, r in temp.iterrows(): st.caption(f"{r['Chapitre']} ({r['J_Type']})")

    st.divider()
    st.subheader("Saisie Notes - Aujourd'hui")
    df_t = st.session_state.data[(pd.to_datetime(st.session_state.data['Date']).dt.date == today) & (st.session_state.data['Dossier'] == choix_dos)].copy()
    if not df_t.empty:
        edited = st.data_editor(df_t[['ID', 'Chapitre', 'J_Type', 'Note', 'Statut']], column_config={"ID": None}, use_container_width=True)
        if st.button("💾 Enregistrer"):
            for _, row in edited.iterrows():
                mask = st.session_state.data['ID'] == row['ID']
                st.session_state.data.loc[mask, 'Note'] = row['Note']
                st.session_state.data.loc[mask, 'Statut'] = row['Statut']
            save_data(st.session_state.data)
            st.rerun()

elif page == "Graphiques":
    st.title("📊 Progression")