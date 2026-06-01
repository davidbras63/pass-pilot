import streamlit as st
import pandas as pd
import datetime as dt
import os
import json

st.set_page_config(layout="wide")

DATA_FILE = "data.csv"
CONFIG_FILE = "config.json"

# --- GESTION DONNÉES & CONFIG ---
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        return df.drop_duplicates()
    return pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note', 'Statut', 'Date_Examen'])

def save_data(df):
    df.drop_duplicates(inplace=True)
    df.to_csv(DATA_FILE, index=False)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f: return json.load(f)
    return {'cours_max': 5, 'cadencier': [1, 3, 7, 14, 30], 'seuils': {1: 12, 3: 12, 7: 14, 14: 14, 30: 16}, 'dossiers': {"PASS": []}}

if 'data' not in st.session_state: st.session_state.data = load_data()
if 'config' not in st.session_state: st.session_state.config = load_config()

# --- SIDEBAR ---
st.sidebar.title("⚙️ Pilot Expert")
with st.sidebar.expander("🛠️ Réglages", expanded=False):
    st.session_state.config['cours_max'] = st.number_input("Max cours/jour", 1, 20, st.session_state.config.get('cours_max', 5))
    cad_str = st.text_input("Cadencier (jours)", ",".join(map(str, st.session_state.config['cadencier'])))
    st.session_state.config['cadencier'] = [int(x.strip()) for x in cad_str.split(",")]
    for j in st.session_state.config['cadencier']:
        st.session_state.config['seuils'][str(j)] = st.slider(f"Seuil Note J{j}", 10, 20, int(st.session_state.config['seuils'].get(str(j), 12)))
    if st.button("💾 Enregistrer"): 
        with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)
        st.rerun()

nom_dossier = st.sidebar.text_input("Nouveau Dossier")
if st.sidebar.button("➕ Créer Dossier") and nom_dossier:
    st.session_state.config['dossiers'][nom_dossier] = []; st.rerun()

choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.config['dossiers'].keys()))
nom_matiere = st.sidebar.text_input("Nom Matière")
if st.sidebar.button("➕ Ajouter Matière") and nom_matiere:
    st.session_state.config['dossiers'][choix_dos].append(nom_matiere); st.rerun()

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
    rattrapages = df_dos[(df_dos['Note'] > 0) & (df_dos['Note'] < 12)]
    
    if not rattrapages.empty:
        st.table(rattrapages[['Matiere', 'Chapitre', 'J_Type', 'Date', 'Note']])
        if st.button("🔄 Réintégrer et purger"):
            for idx, row in rattrapages.iterrows():
                new_r = row.copy(); new_r['Date'] = dt.date.today(); new_r['J_Type'] = 'RAT'; new_r['Note'] = 0
                st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_r])])
            st.session_state.data = st.session_state.data.drop(rattrapages.index)
            save_data(st.session_state.data); st.rerun()

# --- PLANNING & SAISIE ---
elif page == "Planning & Saisie":
    import uuid

    # --- 1. AJOUT ---
    with st.expander("✍️ Ajouter Chapitre"):
        with st.form("Add"):
            mat = st.selectbox("Matière", st.session_state.config['dossiers'].get(choix_dos, []))
            chap = st.text_input("Titre")
            d0 = st.date_input("Date J0")
            dex = st.date_input("Date Examen", value=None)
            if st.form_submit_button("Générer"):
                for j in [0] + st.session_state.config['cadencier']:
                    date_j = d0 + dt.timedelta(days=j)
                    if date_j <= dex:
                        st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([{
                            'ID': str(uuid.uuid4()), 'Dossier': choix_dos, 'Matiere': mat, 
                            'Chapitre': chap, 'J_Type': f'J{j}', 'Date': str(date_j), 
                            'Note': 0, 'Statut': 'À faire'
                        }])])
                save_data(st.session_state.data); st.rerun()

    # --- 2. AFFICHAGE ET SAISIE ---
    st.divider()
    cols = st.columns(7)
    dates = [dt.date.today() + dt.timedelta(days=x) for x in range(7)]
    
    for i, day in enumerate(dates):
        with cols[i]:
            st.markdown(f"**{day.strftime('%d/%m')}**")
            # Filtrage propre sur la date et le dossier
            mask = (pd.to_datetime(st.session_state.data['Date']).dt.date == day) & \
                   (st.session_state.data['Dossier'] == choix_dos)
            df_day = st.session_state.data[mask]
            
            if not df_day.empty:
                # Boutons de validation
                for _, r in df_day.iterrows():
                    if st.button(f"✅ {r['Chapitre']} ({r['J_Type']})", key=f"btn_{r['ID']}"):
                        st.session_state.data.loc[st.session_state.data['ID'] == r['ID'], 'Statut'] = 'Fait'
                        save_data(st.session_state.data); st.rerun()
                
                # Édition des notes
                edited = st.data_editor(
                    df_day[['ID', 'Chapitre', 'J_Type', 'Note']],
                    column_config={"ID": None}, hide_index=True
                )
                if st.button("💾", key=f"save_{day}"):
                    for _, row in edited.iterrows():
                        st.session_state.data.loc[st.session_state.data['ID'] == row['ID'], 'Note'] = row['Note']
                    save_data(st.session_state.data); st.success("OK"); st.rerun()
            else:
                st.info("---")
            
            # SAISIE NOTES (Le tableau réapparaît ici)
            if not df_day.empty:
                st.caption("Notes")
                # On affiche Chapitre, Type et Note pour la saisie
                edited = st.data_editor(
                    df_day[['ID', 'Chapitre', 'J_Type', 'Note']], 
                    column_config={"ID": None, "Chapitre": st.column_config.TextColumn(disabled=True), "J_Type": st.column_config.TextColumn(disabled=True)}, 
                    hide_index=True
                )
                
                if st.button("💾", key=f"save_{day}"):
                    for _, row in edited.iterrows():
                        st.session_state.data.loc[st.session_state.data['ID'] == row['ID'], 'Note'] = row['Note']
                    save_data(st.session_state.data)
                    st.success("Enregistré")
                    st.rerun()

# --- GRAPHIQUES ---
elif page == "Graphiques":
    st.title("📊 Progression")
    for mat in st.session_state.config['dossiers'].get(choix_dos, []):
        st.subheader(f"📚 {mat}")
        st.table(st.session_state.data[(st.session_state.data['Matiere'] == mat) & (st.session_state.data['Note'] > 0)][['Date', 'Note']].tail(3))
