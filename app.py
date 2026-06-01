import streamlit as st
import pandas as pd
import datetime as dt
import os
import json

st.set_page_config(layout="wide")

DATA_FILE = "data.csv"
CONFIG_FILE = "config.json"

# --- UTILITAIRES ---
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
        return df.drop_duplicates(subset=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date'])
    return pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note', 'Statut', 'Date_Examen'])

def save_data(df):
    df.drop_duplicates(inplace=True)
    df.to_csv(DATA_FILE, index=False)

# --- CONFIG ---
if 'data' not in st.session_state: st.session_state.data = load_data()
if 'config' not in st.session_state: 
    st.session_state.config = {'dossiers': {"PASS": []}, 'cadencier': [1, 3, 7, 14, 30], 'seuils': {1: 12, 3: 12, 7: 14, 14: 14, 30: 16}}

# --- SIDEBAR ---
st.sidebar.title("⚙️ Pilot Expert")
choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.config['dossiers'].keys()))
if st.sidebar.button("➕ Ajouter Matière"): st.session_state.config['dossiers'][choix_dos].append("Nouvelle"); st.rerun()

page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])

# --- DASHBOARD ---
if page == "Dashboard":
    st.title("🎯 Dashboard")
    df_dos = st.session_state.data[st.session_state.data['Dossier'] == choix_dos]
    st.subheader("⚠️ Rattrapages")
    rattrapages = df_dos[(df_dos['Note'] > 0) & (df_dos['Note'] < 12)]
    
    if not rattrapages.empty:
        st.table(rattrapages[['Matiere', 'Chapitre', 'J_Type', 'Note']].head(10))
        if st.button("🔄 Réintégrer Rattrapages"):
            for idx, row in rattrapages.iterrows():
                new_row = row.copy()
                new_row['Date'] = dt.date.today()
                new_row['J_Type'] = 'RAT'
                new_row['Statut'] = 'À faire'
                st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])])
            st.session_state.data.at[idx, 'Statut'] = 'Fait'
            save_data(st.session_state.data); st.rerun()
    else: st.write("Aucun rattrapage.")

# --- PLANNING ---
elif page == "Planning & Saisie":
    with st.expander("➕ Ajouter Chapitre"):
        with st.form("Add"):
            mat = st.selectbox("Matière", st.session_state.config['dossiers'].get(choix_dos, []))
            chap = st.text_input("Nom Chapitre")
            d0 = st.date_input("Date J0")
            dex = st.date_input("Date Examen", value=None)
            if st.form_submit_button("Générer"):
                if not dex: st.error("La date d'examen est obligatoire !")
                else:
                    for j in [0] + st.session_state.config['cadencier']:
                        st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([{'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': f'J{j}', 'Date': d0 + dt.timedelta(days=j), 'Note': 0, 'Statut': 'À faire', 'Date_Examen': dex}])])
                    save_data(st.session_state.data); st.rerun()

    # Affichage Planning
    cols = st.columns(7)
    for i, day in enumerate([dt.date.today() + dt.timedelta(days=x) for x in range(7)]):
        with cols[i]:
            st.markdown(f"**{day.strftime('%d/%m')}**")
            for idx, r in st.session_state.data[st.session_state.data['Date'] == day].iterrows():
                if st.button(f"{r['Matiere']}", key=f"v_{idx}"):
                    st.session_state.data.at[idx, 'Statut'] = 'Fait'
                    save_data(st.session_state.data); st.rerun()

    st.subheader("📝 Saisie")
    df_today = st.session_state.data[st.session_state.data['Date'] == dt.date.today()]
    if not df_today.empty:
        edited = st.data_editor(df_today[['Matiere', 'Chapitre', 'Note']].head(5))
        if st.button("Enregistrer"): st.session_state.data.update(edited); save_data(st.session_state.data); st.rerun()

# --- GRAPHIQUES ---
elif page == "Graphiques":
    for mat in st.session_state.config['dossiers'].get(choix_dos, []):
        st.table(st.session_state.data[st.session_state.data['Matiere'] == mat][['Date', 'Note']].tail(5))