import streamlit as st
import pandas as pd
import datetime as dt
import os
import json

st.set_page_config(layout="wide")

DATA_FILE = "data.csv"
CONFIG_FILE = "config.json"

# --- CHARGEMENT ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce').dt.date
            df['Note'] = pd.to_numeric(df['Note'], errors='coerce').fillna(0)
            if 'Statut' not in df.columns: df['Statut'] = 'À faire'
            # Nettoyage automatique des doublons stricts
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
    return {'dossiers': {"PASS": []}, 'cadencier': [1, 3, 7, 14, 30]}

if 'data' not in st.session_state: st.session_state.data = load_data()
if 'config' not in st.session_state: st.session_state.config = load_config()

# --- SIDEBAR ---
st.sidebar.title("⚙️ Pilot Expert")
choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.config['dossiers'].keys()))

if st.sidebar.button("➕ Ajouter Matière"):
    mat = st.sidebar.text_input("Nom Matière")
    if mat: st.session_state.config['dossiers'][choix_dos].append(mat); st.rerun()

page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])

# --- DASHBOARD ---
if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    for m in st.session_state.config['dossiers'].get(choix_dos, []):
        c1, c2 = st.columns([4, 1])
        c1.info(f"📚 {m}")
        if c2.button("🗑️", key=f"del_{m}"): st.session_state.config['dossiers'][choix_dos].remove(m); st.rerun()

# --- PLANNING & SAISIE ---
elif page == "Planning & Saisie":
    st.title("🗓️ Planning & Saisie")
    with st.expander("➕ Ajouter Chapitre"):
        with st.form("Add"):
            mat = st.selectbox("Matière", st.session_state.config['dossiers'].get(choix_dos, []))
            chap = st.text_input("Nom Chapitre")
            d0 = st.date_input("Date J0")
            ex = st.date_input("Date Examen", value=None)
            if st.form_submit_button("Générer"):
                for j in [0] + st.session_state.config.get('cadencier', [1, 3, 7]):
                    d = d0 + dt.timedelta(days=j)
                    new_row = {'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': f'J{j}', 'Date': d, 'Note': 0, 'Statut': 'À faire'}
                    st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=True)
                save_data(st.session_state.data); st.rerun()

    st.subheader("Planning Visuel")
    df_dos = st.session_state.data[st.session_state.data['Dossier'] == choix_dos].copy()
    
    cols = st.columns(7)
    for i, day in enumerate([dt.date.today() + dt.timedelta(days=x) for x in range(7)]):
        with cols[i]:
            st.markdown(f"**{day.strftime('%d/%m')}**")
            for idx, r in df_dos[df_dos['Date'] == day].iterrows():
                color = "red" if r.get('Statut') == 'À faire' else "green"
                with st.expander(f":{color}[{r['Matiere']} - {r['J_Type']}]"):
                    st.write(f"Chapitre: **{r['Chapitre']}**")
                    if st.button("✅ Valider", key=f"val_{idx}"):
                        st.session_state.data.at[idx, 'Statut'] = 'Fait'
                        save_data(st.session_state.data); st.rerun()

    st.subheader("📝 Saisie des notes")
    edited_df = st.data_editor(df_dos[['Matiere', 'Chapitre', 'J_Type', 'Note', 'Statut']], key="notes_editor")
    if st.button("💾 Enregistrer Notes"):
        st.session_state.data.update(edited_df)
        save_data(st.session_state.data); st.rerun()

# --- GRAPHIQUES ---
elif page == "Graphiques":
    st.title("📊 Progression par Matière")
    df_graph = st.session_state.data[(st.session_state.data['Dossier'] == choix_dos) & (st.session_state.data['Note'] > 0)]
    for mat in df_graph['Matiere'].unique():
        st.markdown(f"**📚 {mat}**")
        st.table(df_graph[df_graph['Matiere'] == mat][['Date', 'Chapitre', 'Note']])