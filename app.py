import streamlit as st
import pandas as pd
import datetime as dt
import os
import json

st.set_page_config(layout="wide")

DATA_FILE = "data.csv"
CONFIG_FILE = "config.json"

def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['Date'] = pd.to_datetime(df['Date'], dayfirst=True).dt.date
        return df
    return pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note'])

def save_data(df): df.to_csv(DATA_FILE, index=False)

def load_config():
    default = {'cours_max': 5, 'cadencier': [1, 3, 7, 14, 30, 60, 90, 120], 
               'seuils': {'1': 12, '3': 12, '7': 14, '14': 14, '30': 16, '60': 16, '90': 18, '120': 18},
               'dossiers': {"PASS": ["UE1", "UE2"]}}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f: return json.load(f)
    return default

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f: json.dump(cfg, f)

if 'data' not in st.session_state: st.session_state.data = load_data()
if 'config' not in st.session_state: st.session_state.config = load_config()

# --- SIDEBAR ---
st.sidebar.title("⚙️ Pilot Expert")
with st.sidebar.expander("🛠️ Réglages", expanded=True):
    st.session_state.config['cours_max'] = st.number_input("Max cours/jour", 1, 20, st.session_state.config.get('cours_max', 5))
    cad_input = st.text_input("Cadencier", ",".join(map(str, st.session_state.config.get('cadencier', [1,3,7]))))
    st.session_state.config['cadencier'] = [int(x.strip()) for x in cad_input.split(",")]
    for j in st.session_state.config['cadencier']:
        st.session_state.config['seuils'][str(j)] = st.slider(f"Seuil J{j}", 10, 20, int(st.session_state.config['seuils'].get(str(j), 12)))
    if st.button("💾 Enregistrer"): save_config(st.session_state.config); st.rerun()

# Gestion Dossiers
if "folder_key" not in st.session_state: st.session_state.folder_key = 0
new_folder = st.sidebar.text_input("Nouveau Dossier", key=f"f_{st.session_state.folder_key}")
if st.sidebar.button("➕ Créer Dossier") and new_folder:
    st.session_state.config['dossiers'][new_folder] = []; save_config(st.session_state.config)
    st.session_state.folder_key += 1; st.rerun()

choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.config['dossiers'].keys()))
new_mat = st.sidebar.text_input("Ajouter Matière", key=f"m_{st.session_state.folder_key}")
if st.sidebar.button("Ajouter Matière") and new_mat: 
    st.session_state.config['dossiers'][choix_dos].append(new_mat); save_config(st.session_state.config); st.rerun()

page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])
df = st.session_state.data[st.session_state.data['Dossier'] == choix_dos].copy()

# --- PAGES ---
if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    st.subheader("⚠️ Rattrapages")
    rattrapages = []
    for _, r in df.iterrows():
        seuil = int(st.session_state.config['seuils'].get(r['J_Type'].replace('J',''), 12))
        if r['Note'] > 0 and r['Note'] < seuil: rattrapages.append(r)
    if rattrapages: st.table(pd.DataFrame(rattrapages))
    else: st.write("Aucun rattrapage nécessaire.")

elif page == "Planning & Saisie":
    st.title("🗓️ Planning & Saisie")
    with st.expander("➕ Ajouter Chapitre"):
        with st.form("Add", clear_on_submit=True):
            mat = st.selectbox("Matière", st.session_state.config['dossiers'].get(choix_dos, []))
            chap = st.text_input("Nom du Chapitre")
            d0 = st.date_input("Date J0")
            ex = st.date_input("Date Examen")
            if st.form_submit_button("Générer"):
                for j in [0] + st.session_state.config['cadencier']:
                    d = d0 + dt.timedelta(days=j)
                    if d <= ex:
                        new_row = {'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': f"J{j}", 'Date': d, 'Note': 0}
                        st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=True)
                save_data(st.session_state.data); st.rerun()
    
    st.subheader(f"📝 Saisie du jour : {dt.date.today().strftime('%d/%m/%Y')}")
    # Filtre uniquement sur aujourd'hui
    df_today = df[df['Date'] == dt.date.today()]
    if not df_today.empty:
        edited = st.data_editor(df_today, column_config={"Note": st.column_config.NumberColumn(min_value=0, max_value=20)}, use_container_width=True)
        if st.button("Enregistrer"):
            st.session_state.data.update(edited); save_data(st.session_state.data); st.rerun()
    else: st.info("Rien de prévu pour aujourd'hui.")

elif page == "Graphiques":
    st.title("📊 Progression")
    df_clean = df[df['Note'] > 0]
    if not df_clean.empty:
        chart_data = df_clean.pivot(index='Date', columns='Matiere', values='Note')
        st.line_chart(chart_data)
