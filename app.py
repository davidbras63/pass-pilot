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
        df = pd.read_csv(DATA_FILE)
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        return df
    return pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note', 'Statut', 'Date_Examen'])

def save_data(df):
    df.drop_duplicates(inplace=True)
    df.to_csv(DATA_FILE, index=False)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f: return json.load(f)
    return {'dossiers': {"PASS": []}, 'cadencier': [1, 3, 7, 14, 30], 'cours_max': 5}

if 'data' not in st.session_state: st.session_state.data = load_data()
if 'config' not in st.session_state: st.session_state.config = load_config()

# --- SIDEBAR & RÉGLAGES ---
st.sidebar.title("⚙️ Pilot Expert")
with st.sidebar.expander("🛠️ Réglages", expanded=True):
    st.session_state.config['cours_max'] = st.number_input("Max cours/jour", 1, 20, st.session_state.config.get('cours_max', 5))
    cad_input = st.text_input("Cadencier (jours)", ",".join(map(str, st.session_state.config['cadencier'])))
    st.session_state.config['cadencier'] = [int(x.strip()) for x in cad_input.split(",")]
    if st.button("💾 Enregistrer"): 
        with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)
        st.rerun()

choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.config['dossiers'].keys()))
if st.sidebar.button("➕ Ajouter Matière"): 
    mat = st.sidebar.text_input("Nom Matière")
    if mat: st.session_state.config['dossiers'][choix_dos].append(mat); st.rerun()

page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])

# --- DASHBOARD & RATTRAPAGE ---
if page == "Dashboard":
    st.title("🎯 Dashboard")
    df_dos = st.session_state.data[st.session_state.data['Dossier'] == choix_dos]
    rattrapages = df_dos[(df_dos['Note'] > 0) & (df_dos['Note'] < 12)]
    
    st.subheader("⚠️ Rattrapages")
    if not rattrapages.empty:
        st.table(rattrapages[['Matiere', 'Chapitre', 'J_Type', 'Date', 'Note']])
        if st.button("🔄 Réintégrer et purger"):
            for idx, row in rattrapages.iterrows():
                new_row = row.copy()
                new_row['Date'] = dt.date.today()
                new_row['J_Type'] = 'RAT'
                st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])])
                st.session_state.data.at[idx, 'Statut'] = 'Fait'
            save_data(st.session_state.data); st.rerun()

# --- PLANNING & SAISIE ---
elif page == "Planning & Saisie":
    with st.expander("➕ Ajouter Chapitre", expanded=True):
        with st.form("Add"):
            mat = st.selectbox("Matière", st.session_state.config['dossiers'].get(choix_dos, []))
            chap = st.text_input("Nom Chapitre")
            d0 = st.date_input("Date J0")
            dex = st.date_input("Date Examen", value=None)
            if st.form_submit_button("Générer"):
                if not dex: st.error("Date examen obligatoire !")
                else:
                    for j in [0] + st.session_state.config['cadencier']:
                        new_r = {'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': f'J{j}', 
                                 'Date': d0 + dt.timedelta(days=j), 'Note': 0, 'Statut': 'À faire', 'Date_Examen': dex}
                        st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_r])])
                    save_data(st.session_state.data); st.rerun()

    # Planning avec déplacement et validation
    cols = st.columns(7)
    for i, day in enumerate([dt.date.today() + dt.timedelta(days=x) for x in range(7)]):
        with cols[i]:
            st.markdown(f"**{day.strftime('%d/%m')}**")
            for idx, r in st.session_state.data[st.session_state.data['Date'] == day].iterrows():
                color = "green" if r['Statut'] == 'Fait' else "red"
                with st.expander(f":{color}[{r['Matiere']} ({r['J_Type']})]"):
                    st.write(f"Chapitre: {r['Chapitre']}")
                    c1, c2 = st.columns(2)
                    if c1.button("✅ Fait", key=f"v_{idx}"):
                        st.session_state.data.at[idx, 'Statut'] = 'Fait'
                        save_data(st.session_state.data); st.rerun()
                    if c2.button("➡️ Déplacer", key=f"d_{idx}"):
                        new_d = st.date_input("Nouvelle date", key=f"date_{idx}")
                        if st.button("Confirmer", key=f"c_{idx}"):
                            st.session_state.data.at[idx, 'Date'] = new_d
                            save_data(st.session_state.data); st.rerun()

    st.subheader("📝 Saisie Notes")
    df_today = st.session_state.data[st.session_state.data['Date'] == dt.date.today()]
    for idx, row in df_today.iterrows():
        new_n = st.slider(f"{row['Matiere']} - {row['Chapitre']}", 0, 20, int(row['Note']), key=f"s_{idx}")
        if new_n != row['Note']:
            st.session_state.data.at[idx, 'Note'] = new_n
            save_data(st.session_state.data)