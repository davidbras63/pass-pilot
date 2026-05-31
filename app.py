import streamlit as st
import pandas as pd
import datetime as dt
import os

st.set_page_config(layout="wide")

# --- PERSISTANCE ---
DATA_FILE = "data.csv"
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
        return df
    return pd.DataFrame(columns=['ID', 'Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note'])

def save_data(df): df.to_csv(DATA_FILE, index=False)

if 'data' not in st.session_state: st.session_state.data = load_data()
if 'dossiers' not in st.session_state:
    st.session_state.dossiers = {"PASS": ["UE1", "UE2"]}
    st.session_state.config = {'cours_max': 5, 'cadencier': [1, 3, 7, 14, 30], 'seuils': {1: 10, 3: 12, 7: 14, 14: 15, 30: 16}}

# --- SIDEBAR (Réglages) ---
st.sidebar.title("⚙️ Pilot Expert")
with st.sidebar.expander("🛠️ Réglages"):
    st.session_state.config['cours_max'] = st.number_input("Max cours/jour", 1, 20, st.session_state.config['cours_max'])
    if st.sidebar.button("Ajouter Dossier"): st.session_state.dossiers["Nouveau"] = []
    
choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.dossiers.keys()))
new_mat = st.sidebar.text_input("Ajouter Matière")
if st.sidebar.button("Ajouter Matière") and new_mat: 
    st.session_state.dossiers[choix_dos].append(new_mat); st.rerun()

page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])
df = st.session_state.data[st.session_state.data['Dossier'] == choix_dos].copy()

# --- PAGES ---
if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    for m in st.session_state.dossiers[choix_dos]:
        col1, col2 = st.columns([4, 1])
        col1.info(f"{m} : {len(df[df['Matiere'] == m])} sessions")
        if col2.button("🗑️", key=f"del_{m}"): st.session_state.dossiers[choix_dos].remove(m); st.rerun()
            
    st.subheader("⚠️ Rattrapages")
    rattrapages = df[df['Note'].astype(str).str.split(',').str[-1].astype(float) < 10] # Exemple seuil
    st.table(rattrapages[['Matiere', 'Chapitre', 'Note']])
    if st.button("🚀 Placer dans les trous"):
        # Logique de placement auto ici
        save_data(st.session_state.data); st.rerun()

elif page == "Planning & Saisie":
    st.title("🗓️ Planning & Saisie")
    # Formulaire ajout
    with st.expander("➕ Ajouter Chapitre"):
        with st.form("Add"):
            mat = st.selectbox("Matière", st.session_state.dossiers[choix_dos])
            chap = st.text_input("Nom")
            d0 = st.date_input("Date J0")
            exam = st.date_input("Exam")
            if st.form_submit_button("Générer"):
                # Règle dimanche bloqué
                for j in [0, 1, 3, 7]: 
                    d = d0 + dt.timedelta(days=j)
                    if d.weekday() != 6: # Pas dimanche
                        # ajout...
                        pass
                save_data(st.session_state.data); st.rerun()
    
    st.subheader("Planning")
    # Planning visuel (7 colonnes)
    cols = st.columns(7)
    # Affichage...
    
    st.subheader("Saisie des notes")
    # Tableau saisie avec virgules
    edited = st.data_editor(df[['ID', 'Matiere', 'Chapitre', 'Note']], use_container_width=True)
    if st.button("Enregistrer"):
        st.session_state.data.update(edited)
        save_data(st.session_state.data); st.rerun()

elif page == "Graphiques":
    st.title("📊 Progression")