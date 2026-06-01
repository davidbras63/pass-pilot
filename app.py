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
            # Suppression stricte des doublons au chargement
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
with st.sidebar.expander("🛠️ Réglages", expanded=True):
    st.session_state.config['cours_max'] = st.number_input("Max cours/jour", 1, 20, st.session_state.config.get('cours_max', 5))
    if st.button("💾 Enregistrer"): 
        with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)
        st.rerun()

choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.config['dossiers'].keys()))
if st.sidebar.button("➕ Créer Dossier"): 
    nom = st.sidebar.text_input("Nom nouveau dossier")
    if nom: st.session_state.config['dossiers'][nom] = []; st.rerun()
if st.sidebar.button("➕ Ajouter Matière"): 
    mat = st.sidebar.text_input("Nom Matière")
    if mat: st.session_state.config['dossiers'][choix_dos].append(mat); st.rerun()

page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])

# --- DASHBOARD (avec rattrapage) ---
if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    # Tableau Rattrapage
    st.subheader("⚠️ Rattrapages")
    df_filtered = st.session_state.data[st.session_state.data['Dossier'] == choix_dos]
    rattrapages = []
    for j in st.session_state.config['cadencier']:
        seuil = float(st.session_state.config['seuils'].get(str(j), 12))
        mask = (df_filtered['J_Type'] == f"J{j}") & (df_filtered['Note'] > 0) & (df_filtered['Note'] < seuil)
        rattrapages.append(df_filtered[mask])
    final = pd.concat(rattrapages) if rattrapages else pd.DataFrame()
    if not final.empty: st.table(final[['Matiere', 'Chapitre', 'J_Type', 'Date', 'Note']])
    else: st.write("Pas de rattrapage.")

# --- PLANNING & SAISIE ---
elif page == "Planning & Saisie":
    st.title("🗓️ Planning & Saisie")
    # Planning Visuel (Doublons supprimés)
    df_dos = st.session_state.data[st.session_state.data['Dossier'] == choix_dos].copy()
    df_dos = df_dos.drop_duplicates(subset=['Matiere', 'Chapitre', 'J_Type', 'Date'])
    
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
    
    # Saisie des notes (Filtré sur le jour J)
    st.subheader("📝 Saisie Notes (Aujourd'hui)")
    df_today = df_dos[df_dos['Date'] == dt.date.today()]
    if not df_today.empty:
        edited = st.data_editor(df_today[['Matiere', 'Chapitre', 'Note']])
        if st.button("Enregistrer"): 
            st.session_state.data.update(edited); save_data(st.session_state.data); st.rerun()

# --- GRAPHIQUES (Petits tableaux) ---
elif page == "Graphiques":
    st.title("📊 Progression")
    for mat in st.session_state.config['dossiers'].get(choix_dos, []):
        st.markdown(f"**📚 {mat}**")
        df_mat = st.session_state.data[(st.session_state.data['Matiere'] == mat) & (st.session_state.data['Note'] > 0)]
        st.table(df_mat[['Date', 'Note']].tail(3))