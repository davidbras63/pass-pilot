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
        try:
            df = pd.read_csv(DATA_FILE)
            df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce').dt.date
            df['Note'] = pd.to_numeric(df['Note'], errors='coerce').fillna(0)
            if 'Statut' not in df.columns: df['Statut'] = 'À faire'
            return df
        except: return pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note', 'Statut', 'Date_Examen'])
    return pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note', 'Statut', 'Date_Examen'])

def save_data(df): df.to_csv(DATA_FILE, index=False)

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f: return json.load(f)
        except: pass
    return {'cours_max': 5, 'cadencier': [1, 3, 7, 14, 30], 'seuils': {'1': 12, '3': 12, '7': 14, '14': 14, '30': 16}, 'dossiers': {"PASS": []}}

if 'data' not in st.session_state: st.session_state.data = load_data()
if 'config' not in st.session_state: st.session_state.config = load_config()

# --- SIDEBAR ---
st.sidebar.title("⚙️ Pilot Expert")
with st.sidebar.expander("🛠️ Réglages", expanded=True):
    st.session_state.config['cours_max'] = st.number_input("Max cours/jour", 1, 20, st.session_state.config.get('cours_max', 5))
    cad_input = st.text_input("Cadencier (jours)", ",".join(map(str, st.session_state.config.get('cadencier', [1, 3, 7]))))
    st.session_state.config['cadencier'] = [int(x.strip()) for x in cad_input.split(",")]
    
    # Réglage des seuils
    for j in st.session_state.config['cadencier']:
        st.session_state.config['seuils'][str(j)] = st.number_input(f"Seuil Note J{j}", 0, 20, int(st.session_state.config['seuils'].get(str(j), 12)))
        
    if st.button("💾 Enregistrer"): 
        with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)
        st.rerun()

choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.config['dossiers'].keys()))
if st.sidebar.button("➕ Créer Dossier"): 
    nom = st.sidebar.text_input("Nom dossier")
    if nom: st.session_state.config['dossiers'][nom] = []; st.rerun()
if st.sidebar.button("➕ Ajouter Matière"): 
    mat = st.sidebar.text_input("Nom Matière")
    if mat: st.session_state.config['dossiers'][choix_dos].append(mat); st.rerun()

page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])

# --- DASHBOARD ---
if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    for m in st.session_state.config['dossiers'].get(choix_dos, []):
        c1, c2 = st.columns([4, 1])
        c1.info(f"📚 {m}")
        if c2.button("🗑️", key=f"del_{m}"): st.session_state.config['dossiers'][choix_dos].remove(m); st.rerun()
    
    st.subheader("⚠️ Rattrapages")
    df_dos = st.session_state.data[st.session_state.data['Dossier'] == choix_dos]
    
    rattrapages = []
    for j in st.session_state.config['cadencier']:
        seuil = float(st.session_state.config['seuils'].get(str(j), 12))
        mask = (df_dos['J_Type'] == f"J{j}") & (df_dos['Note'] > 0) & (df_dos['Note'] < seuil)
        rattrapages.append(df_dos[mask])
    
    final = pd.concat(rattrapages) if rattrapages else pd.DataFrame()
    
    if not final.empty:
        st.table(final[['Matiere', 'Chapitre', 'J_Type', 'Date', 'Note']])
        if st.button("🔄 Réintégrer et purger"):
            # Ajouter au planning
            for idx, row in final.iterrows():
                new_r = {'Dossier': choix_dos, 'Matiere': row['Matiere'], 'Chapitre': f"RAT: {row['Chapitre']}", 
                         'J_Type': 'RAT', 'Date': dt.date.today(), 'Note': 0, 'Statut': 'À faire', 'Date_Examen': row['Date_Examen']}
                st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_r])], ignore_index=True)
                # Purger l'ancien
                st.session_state.data.at[idx, 'Note'] = 0 # Annule le déclencheur
                st.session_state.data.at[idx, 'Statut'] = 'Fait'
            save_data(st.session_state.data); st.rerun()
    else: st.write("Pas de rattrapage en cours.")

# --- PLANNING & SAISIE ---
elif page == "Planning & Saisie":
    st.title("🗓️ Planning & Saisie")
    with st.expander("➕ Ajouter Chapitre", expanded=True):
        with st.form("Add"):
            mat = st.selectbox("Matière", st.session_state.config['dossiers'].get(choix_dos, []))
            chap = st.text_input("Nom Chapitre")
            d0 = st.date_input("Date J0")
            dex = st.date_input("Date Examen", value=dt.date.today() + dt.timedelta(days=90))
            if st.form_submit_button("Générer Planning"):
                for j in [0] + st.session_state.config['cadencier']:
                    new_r = {'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': f'J{j}', 
                             'Date': d0 + dt.timedelta(days=j), 'Note': 0, 'Statut': 'À faire', 'Date_Examen': dex}
                    st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_r])], ignore_index=True)
                save_data(st.session_state.data); st.rerun()

    st.subheader("Planning Visuel")
    df_visu = st.session_state.data[st.session_state.data['Dossier'] == choix_dos].drop_duplicates()
    cols = st.columns(7)
    for i, day in enumerate([dt.date.today() + dt.timedelta(days=x) for x in range(7)]):
        with cols[i]:
            st.markdown(f"**{day.strftime('%d/%m')}**")
            for idx, r in df_visu[df_visu['Date'] == day].iterrows():
                color = "red" if r['Statut'] == 'À faire' else "green"
                with st.expander(f":{color}[{r['Matiere']} - {r['J_Type']}]"):
                    st.write(f"Chapitre: **{r['Chapitre']}**")
                    if st.button("✅ Valider", key=f"val_{idx}"):
                        st.session_state.data.at[idx, 'Statut'] = 'Fait'
                        save_data(st.session_state.data); st.rerun()
    
    st.subheader("📝 Saisie des notes (Aujourd'hui)")
    df_today = df_visu[df_visu['Date'] == dt.date.today()]
    if not df_today.empty:
        edited = st.data_editor(df_today[['Matiere', 'Chapitre', 'Note']], key="editor_today")
        if st.button("Enregistrer Notes"): st.session_state.data.update(edited); save_data(st.session_state.data); st.rerun()

# --- GRAPHIQUES ---
elif page == "Graphiques":
    st.title("📊 Progression")
    for mat in st.session_state.config['dossiers'].get(choix_dos, []):
        st.markdown(f"**📚 {mat}**")
        df_m = st.session_state.data[(st.session_state.data['Matiere'] == mat) & (st.session_state.data['Note'] > 0)]
        st.table(df_m[['Date', 'Note']].tail(3))