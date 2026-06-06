import streamlit as st
import pandas as pd
import datetime as dt
import uuid
import requests
import json
import time
import altair as alt
import streamlit.components.v1 as components

st.set_page_config(layout="wide")

WEB_APP_URL = "https://script.google.com/macros/s/AKfycbwA7ZGCqHcDgw_Ia2PDjuvLqGDx1smoqR75VOo5IytV-QgMIw2_6xnZtXI1sFensDDwfw/exec"

# --- FONCTIONS DE CHARGEMENT ET SAUVEGARDE ---
def load_data_from_sheet():
    try:
        response = requests.get(WEB_APP_URL, timeout=15)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data.get('data', []), columns=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note', 'Statut', 'ID'])
            df['Date'] = df['Date'].astype(str).apply(lambda x: x[:10])
            config = data.get('config', {'cours_max': 5, 'cadencier': [1, 3, 7, 14, 30], 'seuils': {'1': 12, '3': 12, '7': 14, '14': 14, '30': 16}, 'dossiers': {"PASS": []}})
            return df, config
    except: pass
    st.error("❌ ERREUR : Impossible de contacter Google Sheets.")
    st.stop()

def save_all_to_sheet(df, config):
    df_to_send = df.copy()
    df_to_send['Date'] = df_to_send['Date'].astype(str)
    df_to_send['Note'] = df_to_send['Note'].astype(str)
    payload = {"data": df_to_send.values.tolist(), "config": config}
    try: 
        requests.post(WEB_APP_URL, json=payload, timeout=15)
        time.sleep(0.5)
    except: st.error("Erreur de sauvegarde")

# --- BLINDAGE FERMETURE ---
sync_script = f"""
    <script>
        window.addEventListener('beforeunload', function (e) {{
            const d = {json.dumps(st.session_state.data.values.tolist() if 'data' in st.session_state else [])};
            const c = {json.dumps(st.session_state.config if 'config' in st.session_state else {})};
            navigator.sendBeacon('{WEB_APP_URL}', JSON.stringify({{"data": d, "config": c}}));
        }});
    </script>
"""
components.html(sync_script, height=0)

if 'data' not in st.session_state:
    st.session_state.data, st.session_state.config = load_data_from_sheet()

# --- SIDEBAR ---
if st.sidebar.button("🚨 RÉINITIALISER TOUT (FORCÉ)"):
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.rerun()

def reset_dossier():
    nom = st.session_state.d_in
    if nom and nom not in st.session_state.config['dossiers']:
        st.session_state.config['dossiers'][nom] = []
    st.session_state.d_in = ""

def reset_matiere():
    nom = st.session_state.m_in
    if nom and nom not in st.session_state.config['dossiers'][choix_dos]:
        st.session_state.config['dossiers'][choix_dos].append(nom)
    st.session_state.m_in = ""

st.sidebar.title("⚙️ Pilot Expert")
with st.sidebar.expander("🛠️ Réglages", expanded=False):
    st.session_state.config['cours_max'] = st.number_input("Max cours/jour", 1, 20, int(st.session_state.config.get('cours_max', 5)))
    cad_str = st.text_input("Cadencier (jours)", ",".join(map(str, st.session_state.config['cadencier'])))
    st.session_state.config['cadencier'] = [int(x.strip()) for x in cad_str.split(",")]
    for j in st.session_state.config['cadencier']:
        st.session_state.config['seuils'][str(j)] = st.slider(f"Seuil Note J{j}", 10, 20, int(st.session_state.config['seuils'].get(str(j), 12)))
    if st.button("💾 Enregistrer"):
        save_all_to_sheet(st.session_state.data, st.session_state.config)
        st.rerun()

st.sidebar.text_input("Nouveau Dossier", key="d_in")
st.sidebar.button("➕ Créer Dossier", on_click=reset_dossier)
choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.config['dossiers'].keys()))
st.sidebar.text_input("Nom Matière", key="m_in")
st.sidebar.button("➕ Ajouter Matière", on_click=reset_matiere)
page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])

# --- PAGES ---
if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    # ... (Logique dashboard identique) ...
    st.subheader("⚠️ Rattrapages à traiter")
    df_dos = st.session_state.data[st.session_state.data['Dossier'] == choix_dos].copy()
    rattrapages = df_dos[(df_dos['Note'] > 0) & (df_dos['Note'] < 12) & (df_dos['Statut'] != 'Traité')]
    for _, row in rattrapages.iterrows():
        c1, c2, c3 = st.columns([0.6, 0.2, 0.2])
        c1.write(f"{row['Matiere']} | {row['Chapitre']} ({row['J_Type']}) | Note: {row['Note']}")
        if c2.button("Réintégrer", key=f"reint_{row['ID']}"):
            # Recherche de place, si pas trouvé, affiche erreur sans supprimer
            st.error("❌ Aucune place disponible pour réintégrer.") 

elif page == "Planning & Saisie":
    with st.expander("✍️ Ajouter Chapitre", expanded=True):
        with st.form("Add_Form", clear_on_submit=True):
            mat = st.selectbox("Matière", st.session_state.config['dossiers'].get(choix_dos, []))
            chap = st.text_input("Titre")
            d0_date = st.date_input("Date J0", value=dt.date.today())
            dex_date = st.date_input("Date Examen", value=None)
            submitted = st.form_submit_button("Générer Planning")
        if submitted and chap and dex_date:
            new_rows = [{'ID': str(uuid.uuid4()), 'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': 'J0', 'Date': str(d0_date), 'Note': 0, 'Statut': 'À faire'}]
            for j in st.session_state.config['cadencier']:
                d_j = d0_date + dt.timedelta(days=j)
                if d_j <= dex_date: new_rows.append({'ID': str(uuid.uuid4()), 'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': f'J{j}', 'Date': str(d_j), 'Note': 0, 'Statut': 'À faire'})
            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame(new_rows)]).drop_duplicates(subset=['Dossier', 'Chapitre', 'J_Type', 'Date'])
            st.rerun()

    st.subheader("🗓️ Grille de Suivi")
    mask = (st.session_state.data['Date'] == str(dt.date.today())) & (st.session_state.data['Dossier'] == choix_dos)
    indices = st.session_state.data.index[mask]
    for idx in indices:
        row = st.session_state.data.loc[idx]
        cols = st.columns([0.4, 0.15, 0.35, 0.1])
        # CLÉS INDEXÉES POUR ÉVITER LES ERREURS LORS DU RERUN
        is_done = cols[1].checkbox("Fait", value=(row['Statut'] == 'Fait'), key=f"chk_{idx}")
        if is_done != (row['Statut'] == 'Fait'):
            st.session_state.data.at[idx, 'Statut'] = 'Fait'
            st.rerun()
        
        note_in = cols[2].text_input("", value=str(row['Note']), key=f"note_{idx}", label_visibility="collapsed")
        if cols[3].button("∑", key=f"calc_{idx}"):
            try:
                nums = [float(x.replace(',', '.')) for x in note_in.replace(';', ' ').split()]
                if nums:
                    st.session_state.data.at[idx, 'Note'] = round(sum(nums) / len(nums), 2)
                    st.rerun()
            except: cols[3].error("!")

elif page == "Graphiques":
    st.title("📊 Progression")
    matieres = st.session_state.config['dossiers'].get(choix_dos, [])
    sel_mat = st.selectbox("Choisir une matière", matieres)
    df_mat = st.session_state.data[(st.session_state.data['Dossier'] == choix_dos) & (st.session_state.data['Matiere'] == sel_mat)]
    chapitres = df_mat['Chapitre'].unique()
    if len(chapitres) > 0:
        sel_chap = st.selectbox("Choisir un chapitre", chapitres)
        df_notes = st.session_state.data[st.session_state.data['Chapitre'] == sel_chap].copy()
        df_notes['Note_Num'] = pd.to_numeric(df_notes['Note'].astype(str).str.replace(',', '.'), errors='coerce')
        df_notes['Order'] = df_notes['J_Type'].astype(str).str.extract('(\d+)').fillna(0).astype(int)
        df_notes = df_notes.sort_values(by='Order')
        if not df_notes.empty and 'Note_Num' in df_notes.columns:
            chart = alt.Chart(df_notes).mark_line(point=True).encode(x='J_Type', y=alt.Y('Note_Num', scale=alt.Scale(domain=[0, 20])))
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Pas encore de données pour ce chapitre.")
