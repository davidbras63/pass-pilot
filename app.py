import streamlit as st
import pandas as pd
import datetime as dt
import os
import json
import uuid
import numpy as np

st.set_page_config(layout="wide")

DATA_FILE = "data.csv"
CONFIG_FILE = "config.json"

# --- GESTION DONNÉES & CONFIG ---
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        return df
    return pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note', 'Statut', 'ID'])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f: return json.load(f)
    return {'cours_max': 5, 'cadencier': [1, 3, 7, 14, 30], 'seuils': {'1': 12, '3': 12, '7': 14, '14': 14, '30': 16}, 'dossiers': {"PASS": []}}

if 'data' not in st.session_state: st.session_state.data = load_data()
if 'config' not in st.session_state: st.session_state.config = load_config()

# --- SIDEBAR ---
st.sidebar.title("⚙️ Pilot Expert")
if 'input_dossier' not in st.session_state: st.session_state.input_dossier = ""
def action_creer_dossier():
    nom = st.session_state.input_dossier
    if nom and nom not in st.session_state.config['dossiers']:
        st.session_state.config['dossiers'][nom] = []
        with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)
        st.session_state.input_dossier = ""

with st.sidebar.expander("🛠️ Réglages"):
    st.session_state.config['cours_max'] = st.number_input("Max cours/jour", 1, 20, st.session_state.config.get('cours_max', 5))
    if st.button("💾 Enregistrer"):
        with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)
        st.rerun()

st.sidebar.text_input("Nouveau Dossier", key="input_dossier")
st.sidebar.button("➕ Créer Dossier", on_click=action_creer_dossier)
dossiers_liste = list(st.session_state.config['dossiers'].keys())
if not dossiers_liste: st.stop()
choix_dos = st.sidebar.selectbox("Dossier", dossiers_liste)
page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])

# --- DASHBOARD ---
if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    st.subheader("⚠️ Rattrapages à traiter")
    df_d = st.session_state.data[st.session_state.data['Dossier'] == choix_dos].copy()
    
    # Filtre strict : Note doit être une valeur réelle, pas NaN, pas zéro
    def est_a_rattraper(row):
        if pd.isna(row['Note']) or str(row['Note']) == 'nan': return False
        try:
            valeurs = [float(n) for n in str(row['Note']).split(',') if n != 'nan']
            if not valeurs or valeurs[-1] == 0: return False
            seuil = int(st.session_state.config['seuils'].get(str(row['J_Type']).replace('J','').replace('RAP','1'), 12))
            return row['Date'] <= dt.date.today() and valeurs[-1] < seuil
        except: return False

    rattrapages = df_d[df_d.apply(est_a_rattraper, axis=1)]
    for _, row in rattrapages.iterrows():
        c1, c2 = st.columns([4, 1])
        c1.write(f"📚 {row['Matiere']} | {row['Chapitre']} ({row['J_Type']}) - Note: {row['Note']}")
        if c2.button("Réintégrer", key=f"btn_{row['ID']}"):
            n_r = {'ID':str(uuid.uuid4()),'Dossier':choix_dos,'Matiere':row['Matiere'],'Chapitre':row['Chapitre'],'J_Type':'RAP','Date':dt.date.today(),'Note':np.nan,'Statut':'À faire'}
            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([n_r])])
            save_data(st.session_state.data); st.rerun()

# --- PLANNING & SAISIE ---
elif page == "Planning & Saisie":
    with st.expander("✍️ Ajouter Chapitre"):
        with st.form("Add_Form", clear_on_submit=True):
            mat = st.selectbox("Matière", st.session_state.config['dossiers'].get(choix_dos, []))
            chap = st.text_input("Titre")
            d0 = st.date_input("Date J0")
            if st.form_submit_button("Générer Planning"):
                if chap and not ((st.session_state.data['Dossier'] == choix_dos) & (st.session_state.data['Chapitre'] == chap)).any():
                    rows = [{'ID': str(uuid.uuid4()), 'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': 'J0', 'Date': d0, 'Note': np.nan, 'Statut': 'À faire'}]
                    for j in st.session_state.config['cadencier']:
                        rows.append({'ID': str(uuid.uuid4()), 'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': f'J{j}', 'Date': d0 + dt.timedelta(days=j), 'Note': np.nan, 'Statut': 'À faire'})
                    st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame(rows)])
                    save_data(st.session_state.data); st.rerun()
                else: st.error("Doublon détecté.")

# --- GRAPHIQUES ---
elif page == "Graphiques":
    mat_list = st.session_state.config['dossiers'].get(choix_dos, [])
    if mat_list:
        mat_sel = st.selectbox("Matière", mat_list)
        chap_list = st.session_state.data[(st.session_state.data['Dossier'] == choix_dos) & (st.session_state.data['Matiere'] == mat_sel)]['Chapitre'].unique()
        if len(chap_list) > 0:
            chap_sel = st.selectbox("Chapitre", chap_list)
            df_c = st.session_state.data[(st.session_state.data['Dossier'] == choix_dos) & (st.session_state.data['Chapitre'] == chap_sel)].copy()
            # Nettoyage : uniquement les notes saisies
            df_clean = df_c[df_c['Note'].notna() & (df_c['Note'] != 'nan') & (df_c['Note'] != 0)]
            if not df_clean.empty:
                st.table(df_clean[['J_Type', 'Date', 'Note']])
