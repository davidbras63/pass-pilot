import streamlit as st
import pandas as pd
import datetime as dt
import os
import json

st.set_page_config(layout="wide")

DATA_FILE = "data.csv"
CONFIG_FILE = "config.json"

# --- CHARGEMENT & NETTOYAGE ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce').dt.date
            df['Note'] = pd.to_numeric(df['Note'], errors='coerce').fillna(0)
            if 'Statut' not in df.columns: df['Statut'] = 'À faire'
            # Nettoyage strict : on ne garde que la première occurrence de chaque couple Matière/Chapitre/J_Type/Date
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
# [Configuration identique - omise pour brièveté]

choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.config['dossiers'].keys()))
# [Boutons ajout identique - omis pour brièveté]

page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])

# --- DASHBOARD & GRAPHIQUES ---
# [Logique Dashboard et Graphiques identique]

# --- PLANNING & SAISIE ---
if page == "Planning & Saisie":
    st.title("🗓️ Planning & Saisie")
    # [Expander Ajouter identique]
    
    st.subheader("Planning Visuel")
    df_dos = st.session_state.data[st.session_state.data['Dossier'] == choix_dos].copy()
    # Nettoyage doublons pour l'affichage visuel
    df_dos = df_dos.drop_duplicates(subset=['Matiere', 'Chapitre', 'J_Type', 'Date'])
    
    cols = st.columns(7)
    for i, day in enumerate([dt.date.today() + dt.timedelta(days=x) for x in range(7)]):
        with cols[i]:
            st.markdown(f"**{day.strftime('%d/%m')}**")
            for idx, r in df_dos[df_dos['Date'] == day].iterrows():
                # Couleur dynamique pour toute la case
                status = r.get('Statut', 'À faire')
                color = "green" if status == 'Fait' else "blue"
                
                # Titre explicite dans l'expander : Matière - Chapitre - Type
                expander_label = f":{color}[{r['Matiere']} - {r['Chapitre']} ({r['J_Type']})]"
                with st.expander(expander_label):
                    st.write(f"Matière: {r['Matiere']}")
                    st.write(f"Chapitre: **{r['Chapitre']}**")
                    if status != 'Fait':
                        if st.button("✅ Valider Révision", key=f"val_{idx}"):
                            st.session_state.data.at[idx, 'Statut'] = 'Fait'
                            save_data(st.session_state.data); st.rerun()
                    else: st.success("Révision terminée !")
    
    st.subheader("📝 Saisie")
    # [Section Saisie identique]