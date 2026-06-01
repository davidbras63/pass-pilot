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
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce').dt.date
            df['Note'] = pd.to_numeric(df['Note'], errors='coerce').fillna(0)
            return df
        except: return pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note'])
    return pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note'])

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

# --- SIDEBAR (RÉGLAGES) ---
st.sidebar.title("⚙️ Pilot Expert")
with st.sidebar.expander("🛠️ Réglages", expanded=True):
    st.session_state.config['cours_max'] = st.number_input("Max cours/jour", 1, 20, st.session_state.config.get('cours_max', 5))
    cad_val = ",".join(map(str, st.session_state.config.get('cadencier', [1, 3, 7])))
    cad_input = st.text_input("Cadencier (jours)", cad_val)
    st.session_state.config['cadencier'] = [int(x.strip()) for x in cad_input.split(",")]
    
    for j in st.session_state.config['cadencier']:
        st.session_state.config['seuils'][str(j)] = st.slider(f"Seuil Note J{j}", 10, 20, int(st.session_state.config['seuils'].get(str(j), 12)))
    
    if st.button("💾 Enregistrer"): 
        with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)
        st.rerun()

choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.config['dossiers'].keys()))
if st.sidebar.button("➕ Créer Dossier"): 
    nom = st.sidebar.text_input("Nom"); 
    if nom: st.session_state.config['dossiers'][nom] = []; st.rerun()
if st.sidebar.button("➕ Ajouter Matière"): 
    mat = st.sidebar.text_input("Nom Matière"); 
    if mat: st.session_state.config['dossiers'][choix_dos].append(mat); st.rerun()

page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])
df = st.session_state.data[st.session_state.data['Dossier'] == choix_dos].copy()

# --- DASHBOARD (RATTRAPAGES) ---
if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    # Affichage matières avec poubelle
    for m in st.session_state.config['dossiers'].get(choix_dos, []):
        c1, c2 = st.columns([4, 1])
        c1.info(f"📚 {m}")
        if c2.button("🗑️", key=f"del_{m}"): st.session_state.config['dossiers'][choix_dos].remove(m); st.rerun()
    
    st.subheader("⚠️ Rattrapages automatiques")
    df['Note'] = pd.to_numeric(df['Note'], errors='coerce').fillna(0)
    rattrapages = []
    for j in st.session_state.config['cadencier']:
        seuil = float(st.session_state.config['seuils'].get(str(j), 12))
        mask = (df['J_Type'] == f"J{j}") & (df['Note'] > 0) & (df['Note'] < seuil)
        rattrapages.append(df[mask])
    final = pd.concat(rattrapages) if rattrapages else pd.DataFrame()
    if not final.empty:
        disp = final.copy()
        disp['Date'] = disp['Date'].apply(lambda x: x.strftime('%d/%m/%Y'))
        st.table(disp[['Matiere', 'Chapitre', 'J_Type', 'Date', 'Note']])
    else: st.write("Aucun rattrapage nécessaire.")

# --- PLANNING & SAISIE (LOGIQUE INTELLIGENTE) ---
elif page == "Planning & Saisie":
    st.title("🗓️ Planning & Saisie")
    with st.expander("➕ Générer Planning Intelligent"):
        with st.form("Gen"):
            mat = st.selectbox("Matière", st.session_state.config['dossiers'].get(choix_dos, []))
            chap = st.text_input("Nom Chapitre")
            d0 = st.date_input("Date J0 (Format JJ/MM/AAAA)")
            ex = st.date_input("Date Examen (Obligatoire)", value=None)
            if st.form_submit_button("Lancer génération"):
                if not ex: st.error("Date examen obligatoire !")
                else:
                    for j in [0] + st.session_state.config['cadencier']:
                        d = d0 + dt.timedelta(days=j)
                        # Logique soupape dimanche : si dimanche, on décale au lundi
                        if d.weekday() == 6: d += dt.timedelta(days=1)
                        if d <= ex:
                            new_row = {'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': f"J{j}", 'Date': d, 'Note': 0}
                            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=True)
                    save_data(st.session_state.data); st.rerun()
    
    st.subheader("Planning & Saisie")
    if not df.empty:
        # Affichage avec data_editor pour saisie directe
        edited = st.data_editor(df[df['Dossier'] == choix_dos])
        if st.button("Enregistrer toutes les notes"): 
            st.session_state.data.update(edited); save_data(st.session_state.data); st.rerun()

# --- GRAPHIQUES ---
elif page == "Graphiques":
    st.title("📊 Progression")
    if not df.empty:
        df['Note'] = pd.to_numeric(df['Note'], errors='coerce').fillna(0)
        df_clean = df[df['Note'] > 0].copy()
        if not df_clean.empty:
            df_clean['Date'] = df_clean['Date'].apply(lambda x: x.strftime('%d/%m/%Y'))
            st.line_chart(df_clean.pivot_table(index='Date', columns='Matiere', values='Note', aggfunc='mean'))