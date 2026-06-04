import streamlit as st
import pandas as pd
import datetime as dt
import uuid
import requests
import plotly.express as px # Import nécessaire pour tes graphiques

st.set_page_config(layout="wide")

WEB_APP_URL = "https://script.google.com/macros/s/AKfycbwA7ZGCqHcDgw_Ia2PDjuvLqGDx1smoqR75VOo5IytV-QgMIw2_6xnZtXI1sFensDDwfw/exec"

def load_data():
    try:
        r = requests.get(WEB_APP_URL, timeout=15)
        if r.status_code == 200:
            data = r.json()
            df = pd.DataFrame(data.get('data', []), columns=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note', 'Statut', 'ID'])
            df['Date'] = pd.to_datetime(df['Date']).dt.date
            return df, data.get('config', {'dossiers': {"PASS": []}, 'seuils': {'1': 12, '3': 12, '7': 14, '14': 14, '30': 16}})
    except: pass
    return pd.DataFrame(), {'dossiers': {"PASS": []}, 'seuils': {'1': 12, '3': 12, '7': 14, '14': 14, '30': 16}}

def save_data(df, config):
    df['Date'] = df['Date'].astype(str)
    try: requests.post(WEB_APP_URL, json={"data": df.values.tolist(), "config": config}, timeout=15)
    except: pass

if 'data' not in st.session_state:
    st.session_state.data, st.session_state.config = load_data()

st.sidebar.title("⚙️ Pilot Expert")
choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.config.get('dossiers', {}).keys()))
page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])

if page == "Dashboard":
    st.title("Dashboard")
    st.subheader("⚠️ Rattrapages à traiter")
    df_dos = st.session_state.data[st.session_state.data['Dossier'] == choix_dos].copy()
    
    def est_en_rattrapage(row):
        try: note = float(str(row['Note']).replace(',', '.'))
        except: note = 0
        j = str(row['J_Type']).replace('J', '')
        seuil = int(st.session_state.config['seuils'].get(j, 12))
        return 0 < note < seuil and row['Statut'] != 'Traité'
    
    rattrapages = df_dos[df_dos.apply(est_en_rattrapage, axis=1)]
    st.table(rattrapages[['Matiere', 'Chapitre', 'J_Type', 'Date', 'Note']])

elif page == "Planning & Saisie":
    with st.expander("✍️ Ajouter Chapitre", expanded=True):
        with st.form("Add_Form", clear_on_submit=True):
            mat = st.selectbox("Matière", st.session_state.config['dossiers'].get(choix_dos, []))
            chap = st.text_input("Titre")
            d0 = st.date_input("Date J0", value=dt.date.today())
            dex = st.date_input("Date Examen", value=None)
            if st.form_submit_button("Générer"):
                new_rows = [{'ID': str(uuid.uuid4()), 'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': 'J0', 'Date': d0, 'Note': 0, 'Statut': 'À faire'}]
                for j in [1,3,7,14,30]:
                    d_j = d0 + dt.timedelta(days=j)
                    if dex and d_j <= dex: new_rows.append({'ID': str(uuid.uuid4()), 'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': f'J{j}', 'Date': d_j, 'Note': 0, 'Statut': 'À faire'})
                st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame(new_rows)])
                save_data(st.session_state.data, st.session_state.config)
                st.rerun()

    st.subheader("Planning Hebdo")
    df_week = st.session_state.data[st.session_state.data['Dossier'] == choix_dos].copy()
    
    for _, r in df_week.iterrows():
        cols = st.columns([0.7, 0.3])
        with cols[0]:
            if st.checkbox(f"{r['Chapitre']} ({r['J_Type']})", value=(r['Statut'] == 'Fait'), key=f"chk_{r['ID']}"):
                st.session_state.data.loc[st.session_state.data['ID'] == r['ID'], 'Statut'] = 'Fait'
            else:
                st.session_state.data.loc[st.session_state.data['ID'] == r['ID'], 'Statut'] = 'À faire'
        with cols[1]:
            nouvelle_date = st.date_input("", value=r['Date'], key=f"cal_{r['ID']}", label_visibility="collapsed")
            if nouvelle_date != r['Date']:
                st.session_state.data.loc[st.session_state.data['ID'] == r['ID'], 'Date'] = nouvelle_date
                save_data(st.session_state.data, st.session_state.config)
                st.rerun()
    
    save_data(st.session_state.data, st.session_state.config)
    
    st.subheader("Saisie Notes")
    df_notes = st.session_state.data[st.session_state.data['Dossier'] == choix_dos].copy()
    df_notes['Note'] = df_notes['Note'].astype(str)
    edited = st.data_editor(df_notes[['ID', 'Chapitre', 'Note']], column_config={"ID": None}, use_container_width=True)
    if st.button("Enregistrer"):
        for _, row in edited.iterrows():
            st.session_state.data.loc[st.session_state.data['ID'] == row['ID'], 'Note'] = str(row['Note'])
        save_data(st.session_state.data, st.session_state.config)
        st.rerun()

elif page == "Graphiques":
    st.title("📊 Graphiques de Progression")
    df_graph = st.session_state.data[st.session_state.data['Dossier'] == choix_dos].copy()
    df_graph['Note'] = pd.to_numeric(df_graph['Note'].astype(str).str.replace(',', '.'), errors='coerce')
    fig = px.line(df_graph, x="Date", y="Note", color="Chapitre", title="Évolution des notes par chapitre")
    st.plotly_chart(fig, use_container_width=True)
