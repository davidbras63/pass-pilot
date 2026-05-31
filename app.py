import streamlit as st
import pandas as pd
import datetime as dt

st.set_page_config(layout="wide")

# --- INITIALISATION ---
if 'dossiers' not in st.session_state:
    st.session_state.dossiers = {"PASS": ["UE1", "UE2"]}
    st.session_state.data = pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'Date', 'Note'])
    st.session_state.cadencier = [1, 3, 7, 14, 30]
    st.session_state.seuils = {1: 10, 3: 12, 7: 14, 14: 15, 30: 16}

# --- SIDEBAR ---
st.sidebar.title("⚙️ Réglages")
# Dossiers et Matières
new_dos = st.sidebar.text_input("Nouveau Dossier")
if st.sidebar.button("Créer Dossier") and new_dos: st.session_state.dossiers[new_dos] = []
choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.dossiers.keys()))

new_mat = st.sidebar.text_input("Nouvelle Matière")
if st.sidebar.button("Ajouter Matière") and new_mat: st.session_state.dossiers[choix_dos].append(new_mat)

# Cadencier et Seuils
with st.sidebar.expander("Réglages Jours & Seuils"):
    cad_input = st.text_input("Cadencier (ex: 1,3,7)", ",".join(map(str, st.session_state.cadencier)))
    st.session_state.cadencier = [int(x.strip()) for x in cad_input.split(",")]
    for j in st.session_state.cadencier:
        st.session_state.seuils[j] = st.slider(f"Seuil J{j}", 0, 20, st.session_state.seuils.get(j, 10))

# --- LOGIQUE ---
df = st.session_state.data[st.session_state.data['Dossier'] == choix_dos]

# --- PAGES ---
page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])

if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    # Résumé Matières + Compteur Chapitres
    st.subheader("État des matières")
    for mat in st.session_state.dossiers[choix_dos]:
        nb = len(df[df['Matiere'] == mat])
        st.write(f"**{mat}** : {nb} chapitre(s) suivi(s)")
    
    st.subheader("⚠️ Alertes Rattrapage")
    st.dataframe(df[(df['Note'] > 0) & (df['Note'] < 10)], use_container_width=True)

elif page == "Planning & Saisie":
    st.title("🗓️ Planning & Saisie")
    
    # Ajout Chapitre
    with st.expander("➕ Ajouter un chapitre"):
        with st.form("Add"):
            mat = st.selectbox("Matière", st.session_state.dossiers[choix_dos])
            nom = st.text_input("Chapitre")
            d0 = st.date_input("Date")
            if st.form_submit_button("Ajouter"):
                st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([{'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': nom, 'Date': d0, 'Note': 0}])], ignore_index=True)
                st.rerun()
    
    # Grille Planning
    cols = st.columns(7)
    for i, day in enumerate([dt.date.today() + dt.timedelta(days=i) for i in range(7)]):
        with cols[i]:
            st.markdown(f"**{day.strftime('%A %d')}**")
            for _, r in df[df['Date'] == day].iterrows():
                st.write(f"- {r['Matiere']}: {r['Chapitre']}")
    
    # Saisie Notes par tableau
    st.subheader("✏️ Saisie des Notes")
    edited_df = st.data_editor(df, num_rows="fixed")
    if st.button("Enregistrer les notes"):
        st.session_state.data.update(edited_df)
        st.rerun()

elif page == "Graphiques":
    st.title("📊 Évolution")
    for m in st.session_state.dossiers[choix_dos]:
        st.subheader(m)
        m_df = df[df['Matiere'] == m]
        if not m_df.empty: st.line_chart(m_df.set_index('Date')['Note'])