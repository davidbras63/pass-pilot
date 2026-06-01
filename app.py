import streamlit as st
import pandas as pd
import datetime as dt
import os
import json

st.set_page_config(layout="wide")

DATA_FILE = "data.csv"
CONFIG_FILE = "config.json"

# --- CHARGEMENT ---
def load_data():
    cols = ['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note']
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            for c in cols:
                if c not in df.columns: df[c] = None
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
            df['Note'] = pd.to_numeric(df['Note'], errors='coerce').fillna(0)
            return df
        except: pass
    return pd.DataFrame(columns=cols)

def save_data(df): df.to_csv(DATA_FILE, index=False)

def load_config():
    default = {'cadencier': [1, 3, 7, 14, 30, 60, 90, 120], 
               'seuils': {'1': 12, '3': 12, '7': 14, '14': 14, '30': 16, '60': 16, '90': 18, '120': 18},
               'dossiers': {"PASS": []}}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f: return json.load(f)
        except: pass
    return default

if 'data' not in st.session_state: st.session_state.data = load_data()
if 'config' not in st.session_state: st.session_state.config = load_config()

# --- SIDEBAR (RÉGLAGES COMPLETS) ---
st.sidebar.title("⚙️ Pilot Expert")
with st.sidebar.expander("🛠️ Réglages Seuils", expanded=True):
    cad_str = ",".join(map(str, st.session_state.config.get('cadencier', [1,3,7])))
    cad_input = st.text_input("Cadencier (jours séparés par une virgule)", cad_str)
    st.session_state.config['cadencier'] = [int(x.strip()) for x in cad_input.split(",")]
    
    for j in st.session_state.config['cadencier']:
        key = str(j)
        st.session_state.config['seuils'][key] = st.slider(f"Seuil Note J{j}", 10, 20, int(st.session_state.config['seuils'].get(key, 12)))
    
    if st.button("💾 Enregistrer Réglages"):
        with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)
        st.rerun()

choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.config['dossiers'].keys()))
page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])
df = st.session_state.data[st.session_state.data['Dossier'] == choix_dos].copy()

# --- DASHBOARD ---
if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    st.subheader("⚠️ Tableau des Rattrapages")
    # Utilisation des seuils configurés
    if not df.empty:
        df['Note'] = pd.to_numeric(df['Note'], errors='coerce')
        rattrapages = pd.DataFrame()
        for j in st.session_state.config['cadencier']:
            seuil = st.session_state.config['seuils'].get(str(j), 12)
            mask = (df['J_Type'] == f"J{j}") & (df['Note'] > 0) & (df['Note'] < seuil)
            rattrapages = pd.concat([rattrapages, df[mask]])
        st.table(rattrapages[['Matiere', 'Chapitre', 'J_Type', 'Date', 'Note']])

# --- PLANNING & SAISIE ---
elif page == "Planning & Saisie":
    st.title("🗓️ Planning & Saisie")
    with st.expander("➕ Ajouter Chapitre"):
        with st.form("Add"):
            mat = st.selectbox("Matière", st.session_state.config['dossiers'].get(choix_dos, []))
            chap = st.text_input("Chapitre")
            d0 = st.date_input("Date J0")
            ex = st.date_input("Date Examen (Obligatoire)", value=None)
            if st.form_submit_button("Générer"):
                if not ex: st.error("Date d'examen obligatoire !")
                else:
                    for j in [0] + st.session_state.config['cadencier']:
                        d = d0 + dt.timedelta(days=j)
                        if d <= ex:
                            new_row = {'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': f"J{j}", 'Date': d, 'Note': 0}
                            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=True)
                    save_data(st.session_state.data); st.rerun()

    st.subheader("Planning Visuel")
    cols = st.columns(7)
    for i, day in enumerate([dt.date.today() + dt.timedelta(days=x) for x in range(7)]):
        with cols[i]:
            st.markdown(f"**{day.strftime('%d/%m')}**")
            for idx, r in df[df['Date'] == day].iterrows():
                with st.expander(f"{r['Matiere']} - {r['Chapitre']} ({r['J_Type']})"):
                    new_date = st.date_input("Décaler", r['Date'], key=f"d_{idx}")
                    if st.button("Valider", key=f"b_{idx}"):
                        st.session_state.data.at[idx, 'Date'] = new_date
                        save_data(st.session_state.data); st.rerun()

    st.subheader("📝 Saisie du jour")
    df_today = df[df['Date'] == dt.date.today()]
    if not df_today.empty:
        edited = st.data_editor(df_today)
        if st.button("Enregistrer"): st.session_state.data.update(edited); save_data(st.session_state.data); st.rerun()

# --- GRAPHIQUES ---
elif page == "Graphiques":
    st.title("📊 Progression")
    if not df.empty:
        df['Note'] = pd.to_numeric(df['Note'], errors='coerce')
        st.line_chart(df[df['Note'] > 0].pivot(index='Date', columns='Matiere', values='Note'))
