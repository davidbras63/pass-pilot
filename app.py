import streamlit as st
import pandas as pd
import datetime as dt
import os, json, uuid, numpy as np
import plotly.graph_objects as go

st.set_page_config(layout="wide")

DATA_FILE = "data.csv"
CONFIG_FILE = "config.json"

# --- CHARGEMENT ---
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        return df
    return pd.DataFrame(columns=['ID', 'Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note', 'Statut'])

def save_data(df): df.to_csv(DATA_FILE, index=False)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f: return json.load(f)
    return {'cours_max': 5, 'cadencier': [1, 3, 7, 14, 30], 'seuils': {'1': 12, '3': 12, '7': 14, '14': 14, '30': 16}, 'dossiers': {}}

if 'data' not in st.session_state: st.session_state.data = load_data()
if 'config' not in st.session_state: st.session_state.config = load_config()

# --- SIDEBAR ---
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
    if mat and mat not in st.session_state.config['dossiers'].get(choix_dos, []):
        st.session_state.config['dossiers'][choix_dos].append(mat)
        with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)
        st.session_state.input_matiere = ""

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
    if st.button("❌ Supprimer ce Dossier"):
        del st.session_state.config['dossiers'][choix_dos]
        with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)
        st.session_state.data = st.session_state.data[st.session_state.data['Dossier'] != choix_dos]
        save_data(st.session_state.data); st.rerun()

    st.subheader("⚠️ Rattrapages à traiter")
    df_d = st.session_state.data[st.session_state.data['Dossier'] == choix_dos]
    for _, row in df_d[df_d['Note'] > 0].iterrows():
        seuil = st.session_state.config['seuils'].get(str(row['J_Type']).replace('J',''), 12)
        if row['Note'] < seuil and row['Date'] <= dt.date.today():
            if st.button(f"Réintégrer {row['Chapitre']} ({row['J_Type']})", key=row['ID']):
                target_date = dt.date.today() + dt.timedelta(days=1)
                new_r = {'ID': str(uuid.uuid4()), 'Dossier': choix_dos, 'Matiere': row['Matiere'], 'Chapitre': row['Chapitre'], 'J_Type': 'RAP', 'Date': target_date, 'Note': 0, 'Statut': 'À faire'}
                st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_r])])
                save_data(st.session_state.data); st.rerun()

# --- PLANNING & SAISIE ---
elif page == "Planning & Saisie":
    with st.expander("✍️ Ajouter Chapitre"):
        with st.form("Add_Form", clear_on_submit=True):
            mat = st.selectbox("Matière", st.session_state.config['dossiers'].get(choix_dos, []))
            chap = st.text_input("Titre")
            d0 = st.date_input("Date J0")
            dex = st.date_input("Date Examen", value=None)
            if st.form_submit_button("Générer"):
                if chap and not ((st.session_state.data['Dossier'] == choix_dos) & (st.session_state.data['Chapitre'] == chap)).any():
                    rows = [{'ID': str(uuid.uuid4()), 'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': 'J0', 'Date': d0, 'Note': 0, 'Statut': 'À faire'}]
                    for j in st.session_state.config['cadencier']:
                        date_j = d0 + dt.timedelta(days=j)
                        if dex is None or date_j <= dex:
                            rows.append({'ID': str(uuid.uuid4()), 'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': f'J{j}', 'Date': date_j, 'Note': 0, 'Statut': 'À faire'})
                    st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame(rows)])
                    save_data(st.session_state.data); st.rerun()
                else: st.error("Doublon détecté.")
    
    st.subheader("🗓️ Planning Hebdomadaire")
    cols = st.columns(7)
    today = dt.date.today()
    start = today - dt.timedelta(days=today.weekday())
    for i, col in enumerate(cols):
        day = start + dt.timedelta(days=i)
        with col:
            st.markdown(f"**{day.strftime('%d/%m')}**")
            df_day = st.session_state.data[(pd.to_datetime(st.session_state.data['Date']).dt.date == day) & (st.session_state.data['Dossier'] == choix_dos)]
            for _, r in df_day.iterrows(): st.caption(f"{r['Chapitre']} ({r['J_Type']})")

# --- GRAPHIQUES ---
elif page == "Graphiques":
    st.title("📊 Progression")
    for mat in st.session_state.config['dossiers'].get(choix_dos, []):
        st.subheader(f"📚 {mat}")
        df_m = st.session_state.data[(st.session_state.data['Matiere'] == mat) & (st.session_state.data['Note'] > 0)]
        if not df_m.empty:
            fig = go.Figure([go.Scatter(x=df_m['Date'], y=df_m['Note'], mode='lines+markers')])
            st.plotly_chart(fig)
            st.table(df_m[['Date', 'Note']].tail(3))