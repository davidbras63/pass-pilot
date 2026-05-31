import streamlit as st
import pandas as pd
import datetime as dt

st.set_page_config(layout="wide")

# --- INITIALISATION ---
if 'init' not in st.session_state:
    st.session_state.dossiers = {"PASS": ["UE1", "UE2"]}
    st.session_state.data = pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'Date', 'Note', 'Intervalle'])
    st.session_state.config = {
        'cours_max': 5,
        'cadencier': [1, 3, 7, 14, 30],
        'seuils': {1: 10, 3: 12, 7: 14, 14: 15, 30: 16}
    }
    st.session_state.init = True

# --- SIDEBAR (Réglages persistants) ---
st.sidebar.title("⚙️ Pilot Expert")
with st.sidebar.expander("🛠️ Réglages"):
    st.session_state.config['cours_max'] = st.number_input("Max cours/jour", 1, 20, st.session_state.config['cours_max'])
    st.write("**Seuils de rattrapage par J**")
    for j in st.session_state.config['cadencier']:
        st.session_state.config['seuils'][j] = st.slider(f"Seuil J{j}", 0, 20, st.session_state.config['seuils'].get(j, 10))

# Gestion Dossiers/Matières
new_dos = st.sidebar.text_input("Ajouter Dossier")
if st.sidebar.button("Créer Dossier") and new_dos:
    st.session_state.dossiers[new_dos] = []
    st.rerun()

choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.dossiers.keys()))
new_mat = st.sidebar.text_input("Ajouter Matière")
if st.sidebar.button("Ajouter Matière") and new_mat:
    st.session_state.dossiers[choix_dos].append(new_mat)
    st.rerun()

# --- NAVIGATION ---
page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Notes", "Suivi Évolution"])

# --- LOGIQUE ---
df = st.session_state.data[st.session_state.data['Dossier'] == choix_dos]

# --- PAGES ---
if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    # Liste des matières
    st.subheader("Matières du dossier")
    st.info(", ".join(st.session_state.dossiers[choix_dos]))
    
    st.subheader("⚠️ Alertes Rattrapage")
    st.dataframe(df[(df['Note'] > 0) & (df['Note'] < 10)], use_container_width=True)

elif page == "Planning & Notes":
    st.title("🗓️ Planning & Saisie")
    # Ajout
    with st.form("Add"):
        mat = st.selectbox("Matière", st.session_state.dossiers[choix_dos])
        nom = st.text_input("Nom Chapitre")
        d0 = st.date_input("Date")
        if st.form_submit_button("Ajouter"):
            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([{'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': nom, 'Date': d0, 'Note': 0, 'Intervalle': 0}])])
            st.rerun()
    # Planning
    cols = st.columns(7)
    for i in range(7):
        day = dt.date.today() + dt.timedelta(days=i)
        with cols[i]:
            st.markdown(f"**{day.strftime('%A %d')}**")
            for _, r in df[df['Date'] == day].iterrows():
                st.write(f"- {r['Matiere']}")
    # Saisie Notes
    if not df.empty:
        id_l = st.number_input("ID ligne (voir tableau)", 0, len(df)-1)
        note = st.slider("Note", 0, 20)
        if st.button("Valider"):
            st.session_state.data.loc[df.index[id_l], 'Note'] = note
            st.rerun()
        st.dataframe(df, use_container_width=True)

elif page == "Suivi Évolution":
    st.title("📊 Évolution Moyenne par Matière")
    for m in st.session_state.dossiers[choix_dos]:
        st.subheader(f"Matière : {m}")
        m_df = df[df['Matiere'] == m]
        if not m_df.empty: 
            st.line_chart(m_df.set_index('Date')['Note'])