import streamlit as st
import pandas as pd
import datetime as dt
import os
import json
import uuid
import plotly.graph_objects as go

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

# --- SIDEBAR (IDENTIQUE) ---
st.sidebar.title("⚙️ Pilot Expert")
if 'input_dossier' not in st.session_state: st.session_state.input_dossier = ""
if 'input_matiere' not in st.session_state: st.session_state.input_matiere = ""

def action_creer_dossier():
    nom = st.session_state.input_dossier
    if nom and nom not in st.session_state.config['dossiers']:
        st.session_state.config['dossiers'][nom] = []
        with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)
        st.session_state.input_dossier = ""

def action_ajouter_matiere():
    mat = st.session_state.input_matiere
    if mat and mat not in st.session_state.config['dossiers'][choix_dos]:
        st.session_state.config['dossiers'][choix_dos].append(mat)
        with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)
        st.session_state.input_matiere = ""

with st.sidebar.expander("🛠️ Réglages", expanded=False):
    st.session_state.config['cours_max'] = st.number_input("Max cours/jour", 1, 20, st.session_state.config.get('cours_max', 5))
    cad_str = st.text_input("Cadencier (jours)", ",".join(map(str, st.session_state.config['cadencier'])))
    st.session_state.config['cadencier'] = [int(x.strip()) for x in cad_str.split(",")]
    for j in st.session_state.config['cadencier']:
        st.session_state.config['seuils'][str(j)] = st.slider(f"Seuil Note J{j}", 10, 20, int(st.session_state.config['seuils'].get(str(j), 12)))
    if st.button("💾 Enregistrer"):
        with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)
        st.rerun()

st.sidebar.text_input("Nouveau Dossier", key="input_dossier")
st.sidebar.button("➕ Créer Dossier", on_click=action_creer_dossier)
dossiers_liste = list(st.session_state.config['dossiers'].keys())
if not dossiers_liste: st.stop()
choix_dos = st.sidebar.selectbox("Dossier", dossiers_liste)
st.sidebar.text_input("Nom Matière", key="input_matiere")
st.sidebar.button("➕ Ajouter Matière", on_click=action_ajouter_matiere)
page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])

# --- DASHBOARD ---
if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    # ... (Supprimer dossier identique) ...
    st.subheader("⚠️ Rattrapages à traiter")
    df_d = st.session_state.data[st.session_state.data['Dossier'] == choix_dos].copy()
    # Filtre : Note existe, date passée, note < seuil
    def check_rattrapage(row):
        try:
            notes = [float(n) for n in str(row['Note']).split(',') if n != 'nan']
            derniere = notes[-1]
            seuil = int(st.session_state.config['seuils'].get(str(row['J_Type']).replace('J','').replace('RAP','1'), 12))
            return row['Date'] <= dt.date.today() and derniere < seuil
        except: return False
    
    rattrapages = df_d[df_d.apply(check_rattrapage, axis=1)]
    if not rattrapages.empty:
        st.table(rattrapages[['Matiere', 'Chapitre', 'J_Type', 'Date', 'Note']])
    else: st.write("Aucun rattrapage en attente.")

# --- PLANNING & SAISIE ---
elif page == "Planning & Saisie":
    with st.expander("✍️ Ajouter Chapitre"):
        with st.form("Add_Form", clear_on_submit=True):
            mat = st.selectbox("Matière", st.session_state.config['dossiers'].get(choix_dos, []))
            chap = st.text_input("Titre")
            d0 = st.date_input("Date J0")
            dex = st.date_input("Date Examen", value=None)
            if st.form_submit_button("Générer"):
                # Vérification unicité J0
                if chap and not ((st.session_state.data['Chapitre'] == chap) & (st.session_state.data['Dossier'] == choix_dos)).any():
                    new_rows = [{'ID': str(uuid.uuid4()), 'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': 'J0', 'Date': d0, 'Note': float('nan'), 'Statut': 'À faire'}]
                    for j in st.session_state.config['cadencier']:
                        if dex and (d0 + dt.timedelta(days=j)) <= dex:
                            new_rows.append({'ID': str(uuid.uuid4()), 'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': f'J{j}', 'Date': d0 + dt.timedelta(days=j), 'Note': float('nan'), 'Statut': 'À faire'})
                    st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame(new_rows)])
                    save_data(st.session_state.data); st.rerun()
                else: st.error("Chapitre déjà existant.")
    
    # Saisie Notes
    today = dt.date.today()
    df_t = st.session_state.data[(pd.to_datetime(st.session_state.data['Date']).dt.date == today) & (st.session_state.data['Dossier'] == choix_dos)]
    if not df_t.empty:
        c_sel = st.selectbox("Chapitre", df_t['Chapitre'].unique())
        row = df_t[df_t['Chapitre'] == c_sel].iloc[0]
        n_val = st.number_input("Nouvelle Note", 0.0, 20.0, 0.0)
        if st.button("Ajouter Note"):
            actuel = str(row['Note'])
            new_note = str(n_val) if (actuel == 'nan' or actuel == 'nan') else actuel + "," + str(n_val)
            st.session_state.data.loc[st.session_state.data['ID'] == row['ID'], 'Note'] = new_note
            save_data(st.session_state.data); st.rerun()

# --- GRAPHIQUES ---
elif page == "Graphiques":
    # ... (Sélecteurs identiques) ...
    df_c = st.session_state.data[(st.session_state.data['Dossier'] == choix_dos) & (st.session_state.data['Chapitre'] == chap_sel)].copy()
    # Nettoyage : retirer les 'nan'
    df_c = df_c[df_c['Note'].notna()]
    # ... (Affichage graphique sur notes valides uniquement) ...
    st.table(df_c[df_c['Note'] != 'nan'][['J_Type', 'Date', 'Note']])