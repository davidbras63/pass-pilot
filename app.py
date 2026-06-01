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
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
        return df
    return pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note'])

def save_data(df): df.to_csv(DATA_FILE, index=False)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f: return json.load(f)
    return {'cadencier': [1, 3, 7, 14, 30, 60, 90, 120], 'seuils': {'1':12, '3':12, '7':14}, 'dossiers': {"PASS": []}}

if 'data' not in st.session_state: st.session_state.data = load_data()
if 'config' not in st.session_state: st.session_state.config = load_config()

# --- SIDEBAR ---
st.sidebar.title("⚙️ Pilot Expert")
choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.config['dossiers'].keys()))
page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])

# --- DASHBOARD ---
if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    # Gestion matières + poubelles
    for m in st.session_state.config['dossiers'].get(choix_dos, []):
        col1, col2 = st.columns([4, 1])
        col1.info(f"📚 {m}")
        if col2.button("🗑️", key=f"del_{m}"):
            st.session_state.config['dossiers'][choix_dos].remove(m)
            with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)
            st.rerun()
    
    st.subheader("⚠️ Tableau des Rattrapages")
    df = st.session_state.data[st.session_state.data['Dossier'] == choix_dos]
    df['Note'] = pd.to_numeric(df['Note'], errors='coerce')
    rattrapages = df[(df['Note'] > 0) & (df['Note'] < 12)]
    st.table(rattrapages)

# --- PLANNING & SAISIE ---
elif page == "Planning & Saisie":
    st.title("🗓️ Planning & Saisie")
    df = st.session_state.data[st.session_state.data['Dossier'] == choix_dos]
    
    with st.expander("➕ Ajouter Chapitre"):
        with st.form("Add"):
            mat = st.selectbox("Matière", st.session_state.config['dossiers'].get(choix_dos, []))
            chap = st.text_input("Chapitre")
            d0 = st.date_input("Date J0")
            if st.form_submit_button("Générer"):
                for j in [0] + st.session_state.config['cadencier']:
                    new_row = {'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': f"J{j}", 'Date': d0 + dt.timedelta(days=j), 'Note': 0}
                    st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=True)
                save_data(st.session_state.data); st.rerun()

    st.subheader("Planning Visuel")
    cols = st.columns(7)
    for i, day in enumerate([dt.date.today() + dt.timedelta(days=x) for x in range(7)]):
        with cols[i]:
            st.markdown(f"**{day.strftime('%d/%m')}**")
            for idx, r in df[df['Date'] == day].iterrows():
                with st.expander(f"{r['Matiere']}"):
                    new_date = st.date_input("Décaler", r['Date'], key=f"d_{idx}")
                    if st.button("Valider", key=f"b_{idx}"):
                        st.session_state.data.at[idx, 'Date'] = new_date
                        save_data(st.session_state.data); st.rerun()

    st.subheader("📝 Saisie")
    df_today = df[df['Date'] == dt.date.today()]
    if not df_today.empty:
        edited = st.data_editor(df_today)
        if st.button("Enregistrer"): st.session_state.data.update(edited); save_data(st.session_state.data); st.rerun()

# --- GRAPHIQUES ---
elif page == "Graphiques":
    st.title("📊 Progression")
    df = st.session_state.data[st.session_state.data['Dossier'] == choix_dos]
    df['Note'] = pd.to_numeric(df['Note'], errors='coerce')
    df_clean = df[df['Note'] > 0]
    if not df_clean.empty:
        st.line_chart(df_clean.pivot(index='Date', columns='Matiere', values='Note'))