import streamlit as st
import pandas as pd
import datetime as dt
import os
import json

st.set_page_config(layout="wide")

DATA_FILE = "data.csv"
CONFIG_FILE = "config.json"

# --- NETTOYAGE ET CHARGEMENT ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            # Conversion stricte
            df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
            df['Note'] = pd.to_numeric(df['Note'], errors='coerce').fillna(0)
            # On supprime les lignes où la date est invalide (NaT)
            df = df.dropna(subset=['Date'])
            df['Date'] = df['Date'].dt.date
            return df
        except: return pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note'])
    return pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note'])

def save_data(df): df.to_csv(DATA_FILE, index=False)

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f: return json.load(f)
        except: pass
    return {'cadencier': [1, 3, 7, 14, 30, 60, 90, 120], 'seuils': {'1': 12, '3': 12, '7': 14}, 'dossiers': {"PASS": []}}

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f: json.dump(cfg, f)

if 'data' not in st.session_state: st.session_state.data = load_data()
if 'config' not in st.session_state: st.session_state.config = load_config()

# --- SIDEBAR (INALTÉRÉE) ---
st.sidebar.title("⚙️ Pilot Expert")
with st.sidebar.expander("🛠️ Réglages"):
    cad_input = st.text_input("Cadencier", ",".join(map(str, st.session_state.config.get('cadencier', [1,3,7]))))
    st.session_state.config['cadencier'] = [int(x.strip()) for x in cad_input.split(",")]
    for j in st.session_state.config['cadencier']:
        st.session_state.config['seuils'][str(j)] = st.slider(f"Seuil J{j}", 10, 20, int(st.session_state.config['seuils'].get(str(j), 12)))
    if st.button("💾 Enregistrer"): save_config(st.session_state.config); st.rerun()

choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.config['dossiers'].keys()))
if st.sidebar.button("➕ Créer Dossier"): st.session_state.config['dossiers'][st.sidebar.text_input("Nom")] = []; save_config(st.session_state.config); st.rerun()
if st.sidebar.button("➕ Ajouter Matière"): st.session_state.config['dossiers'][choix_dos].append(st.sidebar.text_input("Nom Matière")); save_config(st.session_state.config); st.rerun()

page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])
df = st.session_state.data[st.session_state.data['Dossier'] == choix_dos].copy()

# --- PAGES ---
if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    # Liste matières
    for m in st.session_state.config['dossiers'].get(choix_dos, []):
        c1, c2 = st.columns([4, 1])
        c1.info(f"📚 {m}")
        if c2.button("🗑️", key=f"del_{m}"): st.session_state.config['dossiers'][choix_dos].remove(m); save_config(st.session_state.config); st.rerun()
    
    st.subheader("⚠️ Rattrapages")
    if not df.empty:
        rattrapages = []
        for j in st.session_state.config['cadencier']:
            seuil = st.session_state.config['seuils'].get(str(j), 12)
            mask = (df['J_Type'] == f"J{j}") & (df['Note'] > 0) & (df['Note'] < seuil)
            rattrapages.append(df[mask])
        if rattrapages:
            final_df = pd.concat(rattrapages)
            st.table(final_df[['Matiere', 'Chapitre', 'J_Type', 'Date', 'Note']])
        else: st.write("Aucun rattrapage.")

elif page == "Planning & Saisie":
    st.title("🗓️ Planning")
    with st.expander("➕ Ajouter"):
        with st.form("Add"):
            mat = st.selectbox("Matière", st.session_state.config['dossiers'].get(choix_dos, []))
            chap = st.text_input("Chapitre")
            d0 = st.date_input("Date J0")
            ex = st.date_input("Date Examen", value=None)
            if st.form_submit_button("Générer"):
                if not ex: st.error("Date examen obligatoire !")
                else:
                    for j in [0] + st.session_state.config['cadencier']:
                        d = d0 + dt.timedelta(days=j)
                        if d <= ex:
                            new_row = {'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': f"J{j}", 'Date': d, 'Note': 0}
                            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=True)
                    save_data(st.session_state.data); st.rerun()

    # Planning visuel
    cols = st.columns(7)
    for i, day in enumerate([dt.date.today() + dt.timedelta(days=x) for x in range(7)]):
        with cols[i]:
            st.markdown(f"**{day.strftime('%d/%m')}**")
            for idx, r in df[df['Date'] == day].iterrows():
                with st.expander(f"{r['Matiere']} ({r['J_Type']})"):
                    if st.button("Valider", key=f"b_{idx}"): st.rerun()

elif page == "Graphiques":
    st.title("📊 Progression")
    if not df.empty:
        df_clean = df[df['Note'] > 0].copy()
        if not df_clean.empty:
            pivot_df = df_clean.pivot_table(index='Date', columns='Matiere', values='Note', aggfunc='mean')
            st.line_chart(pivot_df)
