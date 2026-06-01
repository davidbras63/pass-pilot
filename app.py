import streamlit as st
import pandas as pd
import datetime as dt
import os, json

st.set_page_config(layout="wide")
DATA_FILE, CONFIG_FILE = "data.csv", "config.json"

# --- CONFIG & DATA ---
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE).drop_duplicates()
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        return df
    return pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note', 'Statut', 'Date_Examen'])

def save_data(df): df.drop_duplicates().to_csv(DATA_FILE, index=False)

if 'data' not in st.session_state: st.session_state.data = load_data()
if 'config' not in st.session_state:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f: st.session_state.config = json.load(f)
    else: st.session_state.config = {'dossiers': {"PASS": []}, 'cadencier': [1, 3, 7, 14, 30], 'seuils': {j: 12 for j in [1, 3, 7, 14, 30]}}

# --- SIDEBAR COMPLÈTE ---
st.sidebar.title("⚙️ Pilot Expert")
with st.sidebar.expander("🛠️ Réglages"):
    cad_str = st.text_input("Cadencier", ",".join(map(str, st.session_state.config['cadencier'])))
    if st.button("💾 Enregistrer"):
        st.session_state.config['cadencier'] = [int(x.strip()) for x in cad_str.split(",")]
        with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)
        st.rerun()

nom_d = st.sidebar.text_input("Nouveau Dossier")
if st.sidebar.button("➕ Créer Dossier") and nom_d:
    st.session_state.config['dossiers'][nom_d] = []; st.rerun()

choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.config['dossiers'].keys()))
nom_m = st.sidebar.text_input("Ajouter Matière")
if st.sidebar.button("➕ Ajouter Matière") and nom_m:
    st.session_state.config['dossiers'][choix_dos].append(nom_m); st.rerun()

page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])

# --- DASHBOARD & PLANNING ---
if page == "Dashboard":
    st.title("🎯 Dashboard")
    for m in st.session_state.config['dossiers'].get(choix_dos, []):
        c1, c2 = st.columns([4, 1])
        c1.info(f"📚 {m}")
        if c2.button("🗑️", key=f"del_{m}"): st.session_state.config['dossiers'][choix_dos].remove(m); st.rerun()
    
    rattrapages = st.session_state.data[(st.session_state.data['Note'] > 0) & (st.session_state.data['Note'] < 12)]
    st.table(rattrapages[['Matiere', 'Chapitre', 'J_Type', 'Note']])
    if st.button("🔄 Réintégrer"):
        for _, r in rattrapages.iterrows():
            new_r = r.copy(); new_r['Date'] = dt.date.today(); new_r['J_Type'] = 'RAT'; new_r['Note'] = 0
            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_r])])
        st.session_state.data = st.session_state.data.drop(rattrapages.index)
        save_data(st.session_state.data); st.rerun()

elif page == "Planning & Saisie":
    with st.expander("✍️ Ajouter Chapitre", expanded=True):
        with st.form("Add"):
            mat = st.selectbox("Matière", st.session_state.config['dossiers'][choix_dos])
            chap = st.text_input("Titre")
            d0, dex = st.date_input("Date J0"), st.date_input("Date Examen")
            if st.form_submit_button("Générer"):
                for j in [0] + st.session_state.config['cadencier']:
                    st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([{'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': f'J{j}', 'Date': d0 + dt.timedelta(days=j), 'Note': 0, 'Statut': 'À faire'}])])
                save_data(st.session_state.data); st.rerun()
    
    # Affichage Planning
    for i, day in enumerate([dt.date.today() + dt.timedelta(days=x) for x in range(7)]):
        st.markdown(f"**{day.strftime('%d/%m')}**")
        df_day = st.session_state.data[(st.session_state.data['Date'] == day) & (st.session_state.data['Dossier'] == choix_dos)]
        for idx, r in df_day.iterrows():
            with st.expander(f"{r['Matiere']} ({r['J_Type']}) - {r['Chapitre']}"):
                if st.button("✅ Fait", key=f"f_{idx}"): st.session_state.data.at[idx, 'Statut'] = 'Fait'; save_data(st.session_state.data); st.rerun()

elif page == "Graphiques":
    for mat in st.session_state.config['dossiers'][choix_dos]:
        st.subheader(f"📊 {mat}")
        st.line_chart(st.session_state.data[(st.session_state.data['Matiere'] == mat) & (st.session_state.data['Note'] > 0)].set_index('Date')['Note'])
