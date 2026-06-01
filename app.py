import streamlit as st
import pandas as pd
import datetime as dt
import os, json

st.set_page_config(layout="wide")
DATA_FILE, CONFIG_FILE = "data.csv", "config.json"

# --- GESTION DONNÉES & CONFIG ---
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        return df.drop_duplicates()
    return pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note', 'Statut', 'Date_Examen'])

def save_data(df):
    df = df.drop_duplicates()
    df.to_csv(DATA_FILE, index=False)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f: return json.load(f)
    return {'dossiers': {"PASS": []}, 'cadencier': [1, 3, 7, 14, 30]}

if 'data' not in st.session_state: st.session_state.data = load_data()
if 'config' not in st.session_state: st.session_state.config = load_config()

# --- SIDEBAR ---
st.sidebar.title("⚙️ Pilot Expert")
with st.sidebar.expander("🛠️ Réglages", expanded=True):
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

for m in st.session_state.config['dossiers'].get(choix_dos, []):
    c1, c2 = st.sidebar.columns([3, 1])
    c1.text(f"📚 {m}")
    if c2.button("🗑️", key=f"del_{m}"): 
        st.session_state.config['dossiers'][choix_dos].remove(m); st.rerun()

page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])

# --- DASHBOARD ---
if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    st.subheader("⚠️ Rattrapages")
    rattrapages = st.session_state.data[(st.session_state.data['Note'] > 0) & (st.session_state.data['Note'] < 12) & (st.session_state.data['Dossier'] == choix_dos)]
    if not rattrapages.empty:
        st.table(rattrapages[['Matiere', 'Chapitre', 'J_Type', 'Date', 'Note']])
        if st.button("🔄 Réintégrer et Purger"):
            for _, r in rattrapages.iterrows():
                new_r = r.copy(); new_r['Date'] = dt.date.today(); new_r['J_Type'] = 'RAT'; new_r['Note'] = 0
                st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_r])])
            st.session_state.data = st.session_state.data.drop(rattrapages.index)
            save_data(st.session_state.data); st.rerun()

# --- PLANNING & SAISIE ---
elif page == "Planning & Saisie":
    with st.expander("✍️ Ajouter Chapitre", expanded=True):
        with st.form("Add"):
            mat = st.selectbox("Matière", st.session_state.config['dossiers'].get(choix_dos, []))
            chap = st.text_input("Titre du Chapitre")
            d0 = st.date_input("Date J0")
            # Modification : Date non pré-remplie (value=None)
            dex = st.date_input("Date Examen", value=None)
            if st.form_submit_button("Générer Planning"):
                # Modification : Date bloquante si non renseignée
                if dex is None:
                    st.error("La date d'examen est obligatoire !")
                else:
                    for j in [0] + st.session_state.config['cadencier']:
                        row = {'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': f'J{j}', 
                               'Date': d0 + dt.timedelta(days=j), 'Note': 0, 'Statut': 'À faire', 'Date_Examen': dex}
                        st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([row])])
                    save_data(st.session_state.data); st.rerun()

    cols = st.columns(7)
    for i, day in enumerate([dt.date.today() + dt.timedelta(days=x) for x in range(7)]):
        with cols[i]:
            st.markdown(f"**{day.strftime('%d/%m')}**")
            for idx, r in st.session_state.data[(st.session_state.data['Date'] == day) & (st.session_state.data['Dossier'] == choix_dos)].iterrows():
                with st.expander(f"{r['Matiere']} ({r['J_Type']})"):
                    st.write(f"📖 **{r['Chapitre']}**")
                    if st.button("✅ Fait", key=f"f_{idx}"): st.session_state.data.at[idx, 'Statut'] = 'Fait'; save_data(st.session_state.data); st.rerun()

    st.subheader("📝 Saisie Notes")
    edited = st.data_editor(st.session_state.data[st.session_state.data['Dossier'] == choix_dos][['Matiere', 'Chapitre', 'J_Type', 'Note']])
    if st.button("Enregistrer"): st.session_state.data.update(edited); save_data(st.session_state.data); st.rerun()

# --- GRAPHIQUES ---
elif page == "Graphiques":
    st.title("📊 Progression")
    for mat in st.session_state.config['dossiers'].get(choix_dos, []):
        st.subheader(f"📚 {mat}")
        st.table(st.session_state.data[(st.session_state.data['Matiere'] == mat) & (st.session_state.data['Note'] > 0)][['Date', 'Note']].tail(3))