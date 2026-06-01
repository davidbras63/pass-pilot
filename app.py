import streamlit as st
import pandas as pd
import datetime as dt
import os

st.set_page_config(layout="wide")

# --- GESTION DES DONNÉES ---
DATA_FILE = "data.csv"
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce').dt.date
        return df
    return pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note'])

def save_data(df): df.to_csv(DATA_FILE, index=False)

if 'data' not in st.session_state: st.session_state.data = load_data()
if 'dossiers' not in st.session_state:
    st.session_state.dossiers = {"PASS": ["UE1", "UE2"]}
    st.session_state.config = {'cours_max': 5, 'cadencier': [1, 3, 7, 14, 30]}

# --- SIDEBAR ---
st.sidebar.title("⚙️ Pilot Expert")

# RÉGLAGES (Simple)
with st.sidebar.expander("🛠️ Réglages"):
    st.session_state.config['cours_max'] = st.number_input("Max cours/jour", 1, 20, st.session_state.config['cours_max'])
    cad_input = st.text_input("Cadencier (ex: 1,3,7,14,30)", ",".join(map(str, st.session_state.config['cadencier'])))
    st.session_state.config['cadencier'] = [int(x.strip()) for x in cad_input.split(",")]

# DOSSIERS & MATIÈRES
new_folder = st.sidebar.text_input("Nouveau Dossier")
if st.sidebar.button("➕ Créer Dossier") and new_folder:
    st.session_state.dossiers[new_folder] = []
    st.rerun()

choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.dossiers.keys()))
new_mat = st.sidebar.text_input("Ajouter Matière")
if st.sidebar.button("Ajouter Matière") and new_mat: 
    st.session_state.dossiers[choix_dos].append(new_mat)
    st.rerun()

page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])
df = st.session_state.data[st.session_state.data['Dossier'] == choix_dos].copy()

# --- PAGES ---
if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    st.table(df[df['Note'] != '0'])

elif page == "Planning & Saisie":
    st.title("🗓️ Planning & Saisie")
    with st.form("Add"):
        c1, c2 = st.columns(2)
        mat = c1.selectbox("Matière", st.session_state.dossiers.get(choix_dos, []))
        chap = c1.text_input("Nom")
        d0 = c2.date_input("Date J0", format="DD/MM/YYYY")
        date_exam = c2.date_input("Date Examen", value=None, format="DD/MM/YYYY")
        if st.form_submit_button("Générer"):
            for j in [0] + st.session_state.config['cadencier']:
                d = d0 + dt.timedelta(days=j)
                if d.weekday() != 6 and (not date_exam or d <= date_exam):
                    new_row = {'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': f"J{j}", 'Date': d, 'Note': '0'}
                    st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=True)
            save_data(st.session_state.data); st.rerun()

    st.subheader("📝 Saisie des Notes")
    edited = st.data_editor(df, use_container_width=True)
    if st.button("Enregistrer"):
        st.session_state.data.update(edited)
        save_data(st.session_state.data); st.rerun()

elif page == "Graphiques":
    st.title("📊 Progression")
