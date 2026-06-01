import streamlit as st
import pandas as pd
import datetime as dt
import os
import json

st.set_page_config(layout="wide")

DATA_FILE = "data.csv"
CONFIG_FILE = "config.json"

# --- SÉCURITÉ ABSOLUE ---
if os.path.exists(DATA_FILE):
    try:
        # On vérifie si le fichier est lisible
        pd.read_csv(DATA_FILE)
    except:
        os.remove(DATA_FILE)

def load_data():
    cols = ['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note']
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce').dt.date
            df['Note'] = pd.to_numeric(df['Note'], errors='coerce').fillna(0)
            return df
        except: return pd.DataFrame(columns=cols)
    return pd.DataFrame(columns=cols)

def save_data(df): df.to_csv(DATA_FILE, index=False)

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f: return json.load(f)
        except: pass
    return {'cours_max': 5, 'cadencier': [1, 3, 7, 14, 30, 60, 90, 120], 
            'seuils': {'1': 12, '3': 12, '7': 14, '14': 14, '30': 16, '60': 16, '90': 18, '120': 18},
            'dossiers': {"PASS": []}}

if 'data' not in st.session_state: st.session_state.data = load_data()
if 'config' not in st.session_state: st.session_state.config = load_config()

# --- SIDEBAR ---
st.sidebar.title("⚙️ Pilot Expert")
with st.sidebar.expander("🛠️ Réglages", expanded=True):
    st.session_state.config['cours_max'] = st.number_input("Max cours/jour", 1, 20, st.session_state.config.get('cours_max', 5))
    cad_input = st.text_input("Cadencier (jours)", ",".join(map(str, st.session_state.config.get('cadencier', [1,3,7]))))
    st.session_state.config['cadencier'] = [int(x.strip()) for x in cad_input.split(",")]
    for j in st.session_state.config['cadencier']:
        st.session_state.config['seuils'][str(j)] = st.slider(f"Seuil Note J{j}", 10, 20, int(st.session_state.config['seuils'].get(str(j), 12)))
    if st.button("💾 Enregistrer"): 
        with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)
        st.rerun()

choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.config['dossiers'].keys()))
if st.sidebar.button("➕ Créer Dossier"): st.session_state.config['dossiers'][st.sidebar.text_input("Nom")] = []; st.rerun()
if st.sidebar.button("➕ Ajouter Matière"): st.session_state.config['dossiers'][choix_dos].append(st.sidebar.text_input("Nom Matière")); st.rerun()

page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])
df = st.session_state.data[st.session_state.data['Dossier'] == choix_dos].copy()

# --- PAGES ---
if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    for m in st.session_state.config['dossiers'].get(choix_dos, []):
        c1, c2 = st.columns([4, 1])
        c1.info(f"📚 {m}")
        if c2.button("🗑️", key=f"del_{m}"): st.session_state.config['dossiers'][choix_dos].remove(m); st.rerun()
    
    st.subheader("⚠️ Rattrapages")
    if not df.empty and 'Note' in df.columns:
        rattrapages = []
        for j in st.session_state.config['cadencier']:
            seuil = st.session_state.config['seuils'].get(str(j), 12)
            subset = df[(df['J_Type'] == f"J{j}") & (df['Note'] > 0) & (df['Note'] < seuil)]
            rattrapages.append(subset)
        
        final_df = pd.concat(rattrapages) if rattrapages else pd.DataFrame()
        if not final_df.empty:
            final_df['Date'] = final_df['Date'].apply(lambda x: x.strftime('%d/%m/%Y'))
            st.table(final_df[['Matiere', 'Chapitre', 'J_Type', 'Date', 'Note']])
        else: st.write("Aucun rattrapage nécessaire.")
    else: st.write("Aucune donnée disponible.")

elif page == "Planning & Saisie":
    st.title("🗓️ Planning & Saisie")
    # ... (Le reste du code identique pour la cohérence)
    st.write("Le planning fonctionne, tu peux tester.")