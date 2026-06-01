import streamlit as st
import pandas as pd
import datetime as dt
import os
import json

st.set_page_config(layout="wide")

# --- FICHIERS ---
DATA_FILE = "data.csv"
CONFIG_FILE = "config.json"

# --- CHARGEMENT ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce').dt.date
            df['Note'] = pd.to_numeric(df['Note'], errors='coerce').fillna(0)
            return df
        except: pass
    return pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note'])

def save_data(df): df.to_csv(DATA_FILE, index=False)

def load_config():
    default = {'cadencier': [1, 3, 7, 14, 30, 60, 90, 120], 
               'seuils': {'1': 12, '3': 12, '7': 14, '14': 14, '30': 16, '60': 16, '90': 18, '120': 18},
               'dossiers': {"PASS": ["UE1"]}}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f: return json.load(f)
        except: return default
    return default

if 'data' not in st.session_state: st.session_state.data = load_data()
if 'config' not in st.session_state: st.session_state.config = load_config()

# --- SIDEBAR ---
st.sidebar.title("⚙️ Pilot Expert")
with st.sidebar.expander("🛠️ Réglages", expanded=True):
    cad_str = ",".join(map(str, st.session_state.config['cadencier']))
    cad_input = st.text_input("Cadencier", cad_str)
    st.session_state.config['cadencier'] = [int(x.strip()) for x in cad_input.split(",")]
    if st.button("💾 Enregistrer"): 
        with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)
        st.rerun()

new_folder = st.sidebar.text_input("Nouveau Dossier")
if st.sidebar.button("➕ Créer Dossier") and new_folder:
    st.session_state.config['dossiers'][new_folder] = []; st.rerun()

choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.config['dossiers'].keys()))
new_mat = st.sidebar.text_input("Ajouter Matière")
if st.sidebar.button("Ajouter Matière") and new_mat: 
    st.session_state.config['dossiers'][choix_dos].append(new_mat); st.rerun()

page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])
df = st.session_state.data[st.session_state.data['Dossier'] == choix_dos].copy()

# --- PAGES ---
if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    st.subheader("⚠️ Rattrapages")
    rattrapages = []
    for _, r in df.iterrows():
        seuil = int(st.session_state.config['seuils'].get(str(r['J_Type']).replace('J',''), 12))
        if 0 < r['Note'] < seuil: rattrapages.append(r)
    if rattrapages: st.table(pd.DataFrame(rattrapages))
    else: st.info("Aucun rattrapage nécessaire.")

elif page == "Planning & Saisie":
    st.title("🗓️ Planning & Saisie")
    with st.expander("➕ Ajouter Chapitre", expanded=True):
        with st.form("Add", clear_on_submit=True):
            c1, c2 = st.columns(2)
            mat = c1.selectbox("Matière", st.session_state.config['dossiers'].get(choix_dos, []))
            chap = c1.text_input("Nom")
            d0 = c2.date_input("Date J0")
            ex = c2.date_input("Date Examen")
            if st.form_submit_button("Générer"):
                for j in [0] + st.session_state.config['cadencier']:
                    d = d0 + dt.timedelta(days=j)
                    if d <= ex:
                        new_row = {'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': f"J{j}", 'Date': d, 'Note': 0}
                        st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=True)
                save_data(st.session_state.data); st.rerun()
    
    st.subheader(f"📝 Saisie du jour ({dt.date.today().strftime('%d/%m/%Y')})")
    df_today = df[df['Date'] == dt.date.today()]
    if not df_today.empty:
        edited = st.data_editor(df_today, use_container_width=True)
        if st.button("Enregistrer"): st.session_state.data.update(edited); save_data(st.session_state.data); st.rerun()

elif page == "Graphiques":
    st.title("📊 Progression")
    df_clean = df[df['Note'] > 0]
    if not df_clean.empty:
        st.line_chart(df_clean.pivot(index='Date', columns='Matiere', values='Note'))
