import streamlit as st
import pandas as pd
import datetime as dt

st.set_page_config(layout="wide")

# --- INITIALISATION UNIFIÉE ---
if 'init_done' not in st.session_state:
    st.session_state.dossiers = {"PASS": ["UE1", "UE2"]}
    st.session_state.data = pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'Date', 'Note'])
    # Initialisation de TOUT ce qui cause les erreurs
    st.session_state.cours_max = 5
    st.session_state.cadencier = [1, 3, 7, 14, 30]
    st.session_state.seuils = {1: 10, 3: 12, 7: 14, 14: 15, 30: 16}
    st.session_state.init_done = True

# --- SIDEBAR ---
st.sidebar.title("⚙️ Réglages")
st.session_state.cours_max = st.sidebar.number_input("Max cours/jour", 1, 20, st.session_state.cours_max)

# Gestion Dossiers
new_dos = st.sidebar.text_input("Nouveau Dossier")
if st.sidebar.button("Créer Dossier") and new_dos: 
    st.session_state.dossiers[new_dos] = []
    st.rerun()

choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.dossiers.keys()))

# --- LOGIQUE ---
df = st.session_state.data[st.session_state.data['Dossier'] == choix_dos]

# --- PAGES ---
page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie"])

if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    for mat in st.session_state.dossiers[choix_dos]:
        nb = len(df[df['Matiere'] == mat])
        st.write(f"**{mat}** : {nb} chapitre(s)")

elif page == "Planning & Saisie":
    st.title("🗓️ Planning & Saisie")
    # Formulaire Ajout
    with st.expander("➕ Ajouter un chapitre"):
        with st.form("Add"):
            mat = st.selectbox("Matière", st.session_state.dossiers[choix_dos])
            nom = st.text_input("Chapitre")
            d0 = st.date_input("Date")
            if st.form_submit_button("Ajouter"):
                new_row = pd.DataFrame([{'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': nom, 'Date': d0, 'Note': 0}])
                st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
                st.rerun()
    
    # Visualisation
    st.dataframe(st.session_state.data, use_container_width=True)
    
    st.subheader("✏️ Saisie Notes (par ID ligne)")
    id_saisie = st.number_input("ID ligne", 0, len(st.session_state.data)-1 if not st.session_state.data.empty else 0)
    note_saisie = st.number_input("Note", 0, 20)
    if st.button("Valider"):
        st.session_state.data.loc[id_saisie, 'Note'] = note_saisie
        st.rerun()