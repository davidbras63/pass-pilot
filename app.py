import streamlit as st
import pandas as pd
import datetime as dt
import os
import json

st.set_page_config(layout="wide")

DATA_FILE = "data.csv"
CONFIG_FILE = "config.json"

# --- CHARGEMENT & CONFIG ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce').dt.date
            df['Note'] = pd.to_numeric(df['Note'], errors='coerce').fillna(0)
            if 'Statut' not in df.columns: df['Statut'] = 'À faire'
            return df
        except: return pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note', 'Statut'])
    return pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note', 'Statut'])

def save_data(df): df.to_csv(DATA_FILE, index=False)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f: return json.load(f)
    return {'dossiers': {"PASS": []}, 'cadencier': [1, 3, 7, 14, 30], 'seuils': {}}

if 'data' not in st.session_state: st.session_state.data = load_data()
if 'config' not in st.session_state: st.session_state.config = load_config()

# --- SIDEBAR ---
st.sidebar.title("⚙️ Pilot Expert")
with st.sidebar.expander("🛠️ Réglages", expanded=True):
    cad_input = st.text_input("Cadencier (jours)", ",".join(map(str, st.session_state.config.get('cadencier', [1, 3, 7]))))
    st.session_state.config['cadencier'] = [int(x.strip()) for x in cad_input.split(",")]
    if st.button("💾 Enregistrer"): 
        with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)
        st.rerun()

choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.config['dossiers'].keys()))
if st.sidebar.button("➕ Créer Dossier"): 
    nom = st.sidebar.text_input("Nom")
    if nom: st.session_state.config['dossiers'][nom] = []; st.rerun()
if st.sidebar.button("➕ Ajouter Matière"): 
    mat = st.sidebar.text_input("Nom Matière")
    if mat: st.session_state.config['dossiers'][choix_dos].append(mat); st.rerun()

page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])

# --- DASHBOARD ---
if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    # Tableau Rattrapage
    st.subheader("⚠️ Rattrapages")
    df_dos = st.session_state.data[st.session_state.data['Dossier'] == choix_dos]
    rattrapages = df_dos[(df_dos['Note'] > 0) & (df_dos['Note'] < 12)] # Exemple seuil fixe
    if not rattrapages.empty:
        st.table(rattrapages[['Matiere', 'Chapitre', 'J_Type', 'Date', 'Note']])
        if st.button("🔄 Générer Rattrapage"):
            for _, row in rattrapages.iterrows():
                new_r = row.copy(); new_r['Date'] = dt.date.today(); new_r['J_Type'] = 'RAT'; new_r['Statut'] = 'À faire'
                st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_r])], ignore_index=True)
            save_data(st.session_state.data); st.rerun()

# --- PLANNING & SAISIE ---
elif page == "Planning & Saisie":
    st.title("🗓️ Planning & Saisie")
    # Ajout
    with st.expander("➕ Ajouter Chapitre"):
        with st.form("Add"):
            mat = st.selectbox("Matière", st.session_state.config['dossiers'].get(choix_dos, []))
            chap = st.text_input("Chapitre")
            d0 = st.date_input("Date J0")
            if st.form_submit_button("Générer"):
                for j in [0] + st.session_state.config.get('cadencier', []):
                    new_r = {'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': f'J{j}', 'Date': d0 + dt.timedelta(days=j), 'Note': 0, 'Statut': 'À faire'}
                    st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_r])], ignore_index=True)
                st.session_state.data = st.session_state.data.drop_duplicates(subset=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date'])
                save_data(st.session_state.data); st.rerun()

    # Planning Visuel (Doublons supprimés)
    st.subheader("Planning Visuel")
    df_visu = st.session_state.data[st.session_state.data['Dossier'] == choix_dos].drop_duplicates(subset=['Matiere', 'Chapitre', 'J_Type', 'Date'])
    cols = st.columns(7)
    for i, day in enumerate([dt.date.today() + dt.timedelta(days=x) for x in range(7)]):
        with cols[i]:
            st.markdown(f"**{day.strftime('%d/%m')}**")
            for idx, r in df_visu[df_visu['Date'] == day].iterrows():
                color = "red" if r['Statut'] == 'À faire' else "green"
                with st.expander(f":{color}[{r['Matiere']} - {r['J_Type']}]"):
                    st.write(f"Chapitre: **{r['Chapitre']}**")
                    if st.button("✅ Valider", key=f"val_{idx}"):
                        st.session_state.data.at[idx, 'Statut'] = 'Fait'
                        save_data(st.session_state.data); st.rerun()

    # Saisie Notes (Filtrée jour J)
    st.subheader("📝 Saisie Notes (Aujourd'hui)")
    df_today = df_visu[df_visu['Date'] == dt.date.today()]
    if not df_today.empty:
        edited = st.data_editor(df_today[['Matiere', 'Chapitre', 'Note']])
        if st.button("Enregistrer"): st.session_state.data.update(edited); save_data(st.session_state.data); st.rerun()

# --- GRAPHIQUES ---
elif page == "Graphiques":
    st.title("📊 Progression")
    for mat in st.session_state.config['dossiers'].get(choix_dos, []):
        st.markdown(f"**📚 {mat}**")
        df_m = st.session_state.data[(st.session_state.data['Matiere'] == mat) & (st.session_state.data['Note'] > 0)]
        st.table(df_m[['Date', 'Note']].tail(3))