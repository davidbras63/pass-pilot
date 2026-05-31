import streamlit as st
import pandas as pd
import datetime as dt
import re

st.set_page_config(page_title="PASS Pilot Expert", layout="wide")

# Initialisation des états
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=['UE', 'Chapitre_Complet', 'Chapitre_Base', 'Type', 'Date', 'Note', 'Nbre_QCM'])
if 'seuils' not in st.session_state:
    st.session_state.seuils = {'J1': 10, 'J3': 12, 'J7': 14, 'J14': 16, 'J30': 18, 'J60': 18, 'J90': 18, 'J120': 18}
if 'intervalles' not in st.session_state:
    st.session_state.intervalles = {'J1': 1, 'J3': 3, 'J7': 7, 'J14': 14, 'J30': 30, 'J60': 60, 'J90': 90, 'J120': 120}

page = st.sidebar.radio("Navigation", ["Dashboard", "Planning (Saisie)", "⚙️ Paramètres", "UE1", "UE2", "UE3", "UE4", "UE5", "UE6", "UE7"])

# --- PARAMÈTRES ---
if page == "⚙️ Paramètres":
    st.title("⚙️ Réglages Personnalisés")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Seuils d'alerte (Note min)")
        for jour in st.session_state.seuils:
            st.session_state.seuils[jour] = st.number_input(f"Seuil {jour}", 0, 20, st.session_state.seuils[jour])
    with col2:
        st.subheader("Intervalles (Jours)")
        for jour in st.session_state.intervalles:
            st.session_state.intervalles[jour] = st.number_input(f"Délai {jour}", 0, 365, st.session_state.intervalles[jour])
    st.success("Modifications prises en compte !")

# --- DASHBOARD ---
elif page == "Dashboard":
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

# --- PLANNING (SAISIE) ---
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
                n = [float(x.strip()) for x in saisie.split(',')]
                st.session_state.data.at[idx, 'Note'] = round(sum(n)/len(n), 1)
                st.session_state.data.at[idx, 'Nbre_QCM'] = len(n)
                st.rerun()
            except: 
                st.error("Format invalide, utilisez des virgules")
    else: 
        st.info("Ajoutez un chapitre pour commencer.")

# --- PAGES UE ---
elif page.startswith("UE"):
    st.title(f"📊 {page}")
    df_ue = st.session_state.data[st.session_state.data['UE'] == page]
    if not df_ue.empty:
        for base in df_ue['Chapitre_Base'].unique():
            st.write(f"### {base}")
            sub = df_ue[df_ue['Chapitre_Base'] == base].sort_values('Date')
            st.line_chart(sub.set_index('Date')['Note'])
    else:
        st.write("Aucune donnée pour cette UE.")