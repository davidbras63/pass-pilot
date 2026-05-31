import streamlit as st
import pandas as pd
import datetime as dt
import re
import plotly.graph_objects as go

# Configuration design
st.set_page_config(page_title="PASS Pilot Expert", layout="wide")
st.markdown("<style>.stApp { background-color: #f8f9fa; }</style>", unsafe_allow_html=True)

# Initialisation des données
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=['UE', 'Chapitre_Complet', 'Chapitre_Base', 'Type', 'Date', 'Note', 'Nbre_QCM'])
if 'seuils' not in st.session_state:
    st.session_state.seuils = {'J1': 10, 'J3': 12, 'J7': 14, 'J14': 16, 'J30': 18, 'J60': 18, 'J90': 18, 'J120': 18}
if 'intervalles' not in st.session_state:
    st.session_state.intervalles = {'J1': 1, 'J3': 3, 'J7': 7, 'J14': 14, 'J30': 30, 'J60': 60, 'J90': 90, 'J120': 120}

# Menu Navigation
page = st.sidebar.radio("Navigation", ["Dashboard", "Planning (Saisie)", "UE1", "UE2", "UE3", "UE4", "UE5", "UE6", "UE7"])

# --- DASHBOARD ---
if page == "Dashboard":
    st.title("🎯 Dashboard de Pilotage")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("⚙️ Seuils (Note min)")
        for j in st.session_state.seuils: st.session_state.seuils[j] = st.number_input(f"Seuil {j}", 0, 20, st.session_state.seuils[j])
    with c2:
        st.subheader("⚙️ Cadencement (J)")
        for j in st.session_state.intervalles: st.session_state.intervalles[j] = st.number_input(f"Intervalle {j} (jours)", 1, 150, st.session_state.intervalles[j])
    
    st.subheader("🚨 Rattrapages urgents")
    df_temp = st.session_state.data.copy()
    df_temp['Seuil'] = df_temp['Type'].map(st.session_state.seuils)
    rattrapages = df_temp[(df_temp['Note'] > 0) & (df_temp['Note'] < df_temp['Seuil'])]
    st.table(rattrapages[['UE', 'Chapitre_Complet', 'Type', 'Note', 'Seuil']])

# --- PLANNING ---
elif page == "Planning (Saisie)":
    st.title("🗓️ Saisie & Répartition")
    max_cours = st.slider("Max cours/jour", 1, 15, 5)
    
    with st.form("Saisie", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1: ue = st.selectbox("UE", ["UE1", "UE2", "UE3", "UE4", "UE5", "UE6", "UE7"])
        with c2: nom = st.text_input("Chapitre (ex: Coeur 1)")
        with c3: d0 = st.date_input("Date")
        if st.form_submit_button("Lancer les rappels"):
            base = re.sub(r'\s*\d+$', '', nom.strip())
            for type_j, delta in st.session_state.intervalles.items():
                date_c = d0 + dt.timedelta(days=delta)
                while len(st.session_state.data[st.session_state.data['Date'] == date_c]) >= max_cours:
                    date_c += dt.timedelta(days=1)
                st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([{
                    'UE': ue, 'Chapitre_Complet': nom, 'Chapitre_Base': base, 
                    'Type': type_j, 'Date': date_c, 'Note': 0, 'Nbre_QCM': 0}])])
            st.rerun()

    st.subheader("📝 Enregistrer des résultats QCM")
    if not st.session_state.data.empty:
        idx = st.number_input("ID ligne", 0, len(st.session_state.data)-1)
        saisie = st.text_input("Tapez les notes (ex: 11, 15, 18)")
        if st.button("Calculer et Enregistrer"):
            try:
                n = [float(x.strip()) for x in saisie.split(',')]
                st.session_state.data.at[idx, 'Note'] = round(sum(n)/len(n), 1)
                st.session_state.data.at[idx, 'Nbre_QCM'] = len(n)
                st.rerun()
            except: st.error("Format invalide")
    else:
        st.info("Le planning est vide. Ajoutez des cours dans la partie 'Lancer les rappels' pour voir les lignes apparaître ici.")
    
    st.dataframe(st.session_state.data)

# --- PAGES UE ---
elif page.startswith("UE"):
    st.title(f"📊 Suivi : {page}")
    df_ue = st.session_state.data[st.session_state.data['UE'] == page]
    for base in df_ue['Chapitre_Base'].unique():
        st.subheader(f"Progression : {base}")
        total = int(df_ue[df_ue['Chapitre_Base'] == base]['Nbre_QCM'].sum())
        c1, c2 = st.columns([2, 1])
        with c1: st.line_chart(df_ue[df_ue['Chapitre_Base'] == base].sort_values('Date').set_index('Date')['Note'])
        with c2:
            fig = go.Figure(go.Indicator(mode="gauge+number", value=total, title={'text': "Volume QCM"},
                            gauge={'axis': {'range': [0, 500]}, 'bar': {'color': "teal"}}))
            st.plotly_chart(fig, use_container_width=True)