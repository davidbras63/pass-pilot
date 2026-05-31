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
        df.columns = df.columns.str.strip() # Nettoie les noms de colonnes
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
        return df
    return pd.DataFrame(columns=['ID', 'Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note'])

def save_data(df): df.to_csv(DATA_FILE, index=False)

if 'data' not in st.session_state: st.session_state.data = load_data()
if 'dossiers' not in st.session_state:
    st.session_state.dossiers = {"PASS": ["UE1", "UE2"]}
    st.session_state.config = {'cours_max': 5, 'cadencier': [1, 3, 7, 14, 30], 'seuils': {1: 10, 3: 12, 7: 14, 14: 15, 30: 16}}

# --- SIDEBAR (Réglages restaurés) ---
st.sidebar.title("⚙️ Pilot Expert")
with st.sidebar.expander("🛠️ Réglages complets"):
    st.session_state.config['cours_max'] = st.number_input("Max cours/jour", 1, 20, st.session_state.config['cours_max'])
    cad_str = st.text_input("Cadencier", ",".join(map(str, st.session_state.config['cadencier'])))
    st.session_state.config['cadencier'] = [int(x.strip()) for x in cad_str.split(",")]

new_dos = st.sidebar.text_input("Créer Dossier")
if st.sidebar.button("Ajouter Dossier") and new_dos: 
    st.session_state.dossiers[new_dos] = []
    st.rerun()

choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.dossiers.keys()))
new_mat = st.sidebar.text_input("Ajouter Matière")
if st.sidebar.button("Ajouter Matière") and new_mat: 
    st.session_state.dossiers[choix_dos].append(new_mat)
    st.rerun()

page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])
df = st.session_state.data[st.session_state.data['Dossier'] == choix_dos].copy() if not st.session_state.data.empty else pd.DataFrame()

# --- PAGES ---
if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    # ... (Ton affichage dashboard original) ...
    st.subheader("⚠️ Rattrapages")
    if not df.empty:
        st.table(df[df['Note'].astype(str).str.contains(',')] if 'Note' in df.columns else df)

elif page == "Planning & Saisie":
    st.title("🗓️ Planning & Saisie")
    # Formulaire d'ajout
    with st.expander("➕ Ajouter Chapitre"):
        with st.form("Add"):
            mat = st.selectbox("Matière", st.session_state.dossiers.get(choix_dos, []))
            chap = st.text_input("Chapitre")
            d0 = st.date_input("Date")
            if st.form_submit_button("Générer"):
                # Règle dimanche bloqué
                if d0.weekday() != 6:
                    new_row = pd.DataFrame([{'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'Date': d0, 'Note': '0'}])
                    st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
                    save_data(st.session_state.data); st.rerun()

    st.subheader("Saisie des notes")
    # Affichage dynamique sans forcer les noms de colonnes pour éviter le KeyError
    edited = st.data_editor(df, use_container_width=True, hide_index=True)
    if st.button("Enregistrer"):
        st.session_state.data.update(edited)
        save_data(st.session_state.data); st.rerun()

elif page == "Graphiques":
    st.title("📊 Progression")