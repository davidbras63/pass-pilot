import streamlit as st
import pandas as pd
import datetime as dt
import re
import plotly.graph_objects as go

st.set_page_config(page_title="PASS Pilot Expert", layout="wide")

# Initialisation
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=['UE', 'Chapitre_Complet', 'Chapitre_Base', 'Type', 'Date', 'Note', 'Nbre_QCM'])
if 'seuils' not in st.session_state:
    st.session_state.seuils = {'J1': 10, 'J3': 12, 'J7': 14, 'J14': 16, 'J30': 18, 'J60': 18, 'J90': 18, 'J120': 18}
if 'intervalles' not in st.session_state:
    st.session_state.intervalles = {'J1': 1, 'J3': 3, 'J7': 7, 'J14': 14, 'J30': 30, 'J60': 60, 'J90': 90, 'J120': 120}

page = st.sidebar.radio("Navigation", ["Dashboard", "Planning (Saisie)", "UE1", "UE2", "UE3", "UE4", "UE5", "UE6", "UE7"])

# --- DASHBOARD COMPACT ---
if page == "Dashboard":
    st.title("🎯 Dashboard")
    c1, c2, c3 = st.columns(3)
    c1.metric("Chapitres", len(st.session_state.data['Chapitre_Base'].unique()))
    c2.metric("QCM total", int(st.session_state.data['Nbre_QCM'].sum()))
    notes_valides = st.session_state.data[st.session_state.data['Note'] > 0]['Note']
    c3.metric("Moyenne", f"{notes_valides.mean():.1f}/20" if not notes_valides.empty else "N/A")
    
    st.subheader("⚠️ Alertes Rattrapage")
    df_temp = st.session_state.data.copy()
    df_temp['Seuil'] = df_temp['Type'].map(st.session_state.seuils)
    alertes = df_temp[(df_temp['Note'] > 0) & (df_temp['Note'] < df_temp['Seuil'])]
    st.dataframe(alertes[['UE', 'Chapitre_Complet', 'Note', 'Seuil']], use_container_width=True)

# --- PLANNING VISUEL ---
elif page == "Planning (Saisie)":
    st.title("🗓️ Mon Planning")
    with st.expander("➕ Ajouter un nouveau chapitre"):
        with st.form("Saisie_Simple", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            ue = c1.selectbox("UE", ["UE1", "UE2", "UE3", "UE4", "UE5", "UE6", "UE7"])
            nom = c2.text_input("Nom du Chapitre")
            d0 = c3.date_input("Date de début")
            if st.form_submit_button("Lancer les rappels"):
                base = re.sub(r'\s*\d+$', '', nom.strip())
                for t, delta in st.session_state.intervalles.items():
                    st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([{
                        'UE': ue, 'Chapitre_Complet': nom, 'Chapitre_Base': base, 
                        'Type': t, 'Date': d0 + dt.timedelta(days=delta), 'Note': 0, 'Nbre_QCM': 0}])])
                st.rerun()

    st.subheader("📅 Calendrier")
    st.dataframe(st.session_state.data.sort_values('Date'), use_container_width=True)
    
    st.subheader("📈 Saisie des Notes")
    if not st.session_state.data.empty:
        idx = st.number_input("ID Ligne (voir tableau)", 0, len(st.session_state.data)-1)
        saisie = st.text_input("Notes (ex: 11, 15, 18)")
        if st.button("Valider la saisie"):
            try:
                n = [float(x.strip()) for x in saisie.
