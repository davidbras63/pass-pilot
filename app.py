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
        df = pd.read_csv(DATA_FILE)
        df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce').dt.date
        return df
    return pd.DataFrame(columns=['ID', 'Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note'])

def load_config():
    default = {'dossiers': {"PASS": ["UE1", "UE2"]}, 'cours_max': 5, 'cadencier': [1, 3, 7, 14, 30], 'seuils': {1: 10, 3: 12, 7: 14, 14: 15, 30: 16}}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f: return json.load(f)
    return default

def save_data(df): df.to_csv(DATA_FILE, index=False)
def save_config(cfg):
    with open(CONFIG_FILE, "w") as f: json.dump(cfg, f)

if 'data' not in st.session_state: st.session_state.data = load_data()
if 'config' not in st.session_state: st.session_state.config = load_config()

# --- SIDEBAR ---
st.sidebar.title("⚙️ Pilot Expert")

with st.sidebar.expander("🛠️ Réglages complets"):
    st.session_state.config['cours_max'] = st.number_input("Max cours/jour", 1, 20, st.session_state.config.get('cours_max', 5))
    cad_str = st.text_input("Cadencier (ex: 1,3,7,14,30)", ",".join(map(str, st.session_state.config.get('cadencier', [1, 3, 7, 14, 30]))))
    st.session_state.config['cadencier'] = [int(x.strip()) for x in cad_str.split(",")]
    
    # Seuils
    for j in st.session_state.config['cadencier']:
        st.session_state.config['seuils'][str(j)] = st.slider(f"Seuil note J{j}", 0, 20, st.session_state.config['seuils'].get(str(j), 10))
    
    if st.button("💾 Enregistrer réglages"):
        save_config(st.session_state.config); st.rerun()

# GESTION DOSSIERS
new_folder = st.sidebar.text_input("Créer un Dossier")
if st.sidebar.button("➕ Créer Dossier") and new_folder:
    st.session_state.config['dossiers'][new_folder] = []
    save_config(st.session_state.config); st.rerun()

choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.config['dossiers'].keys()))
new_mat = st.sidebar.text_input("Ajouter Matière")
if st.sidebar.button("Ajouter Matière") and new_mat: 
    st.session_state.config['dossiers'][choix_dos].append(new_mat)
    save_config(st.session_state.config); st.rerun()

page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])
df = st.session_state.data[st.session_state.data['Dossier'] == choix_dos].copy()

# --- PAGES ---
if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    for m in st.session_state.config['dossiers'][choix_dos]:
        col1, col2 = st.columns([4, 1])
        col1.info(f"📚 {m}")
        if col2.button("🗑️", key=f"del_{m}"): 
            st.session_state.config['dossiers'][choix_dos].remove(m)
            save_config(st.session_state.config); st.rerun()
    st.subheader("⚠️ Tableau des Rattrapages")
    st.table(df[df['Note'] != '0'])
    if st.button("🚀 Générer saisie intelligente"): save_data(st.session_state.data); st.rerun()

elif page == "Planning & Saisie":
    st.title("🗓️ Planning & Saisie")
    with st.expander("➕ Ajouter Chapitre", expanded=True):
        with st.form("Add"):
            c1, c2 = st.columns(2)
            mat = c1.selectbox("Matière", st.session_state.config['dossiers'].get(choix_dos, []))
            chap = c1.text_input("Nom")
            d0 = c2.date_input("Date J0", format="DD/MM/YYYY")
            date_exam = c2.date_input("Date Examen", value=None, format="DD/MM/YYYY")
            if st.form_submit_button("Générer"):
                if not date_exam: st.error("⚠️ Date examen obligatoire !")
                else:
                    for j in [0] + st.session_state.config['cadencier']:
                        d = d0 + dt.timedelta(days=j)
                        if d.weekday() != 6 and d <= date_exam:
                            new_row = {'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': f"J{j}", 'Date': d, 'Note': '0'}
                            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=True)
                    save_data(st.session_state.data); st.rerun()

    st.subheader("Planning Visuel")
    cols = st.columns(7)
    for i, day in enumerate([dt.date.today() + dt.timedelta(days=x) for x in range(7)]):
        with cols[i]:
            st.markdown(f"**{day.strftime('%d/%m')}**")
            for _, r in df[df['Date'] == day].iterrows():
                st.caption(f"🎯 {r['Matiere']} : {r['Chapitre']}")
    st.write("---")
    st.subheader("📝 Saisie des Notes")
    edited = st.data_editor(df, use_container_width=True)
    if st.button("Enregistrer"):
        st.session_state.data.update(edited)
        save_data(st.session_state.data); st.rerun()

elif page == "Graphiques":
    st.title("📊 Progression")
