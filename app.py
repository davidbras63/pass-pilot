import streamlit as st
import pandas as pd
import datetime as dt

st.set_page_config(layout="wide")

# --- INITIALISATION ---
if 'v3_init' not in st.session_state:
    st.session_state.dossiers = {"PASS": ["UE1", "UE2"]}
    st.session_state.data = pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'Date', 'Note'])
    st.session_state.cadencier = [1, 3, 7, 14, 30]
    st.session_state.seuils = {j: 10 for j in st.session_state.cadencier}
    st.session_state.v3_init = True

# --- SIDEBAR ---
st.sidebar.title("⚙️ Pilot Expert")
with st.sidebar.expander("🛠️ Réglages (Cadencier & Seuils)"):
    cad_str = st.text_input("Jours (ex: 1,3,7,14,30,60,90)", ",".join(map(str, st.session_state.cadencier)))
    st.session_state.cadencier = [int(x.strip()) for x in cad_str.split(",")]
    st.write("**Seuils de rattrapage par J**")
    for j in st.session_state.cadencier:
        if j not in st.session_state.seuils: st.session_state.seuils[j] = 10
        st.session_state.seuils[j] = st.slider(f"Seuil J{j}", 0, 20, st.session_state.seuils[j])

choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.dossiers.keys()))
page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])

# --- LOGIQUE ---
df = st.session_state.data[st.session_state.data['Dossier'] == choix_dos]

# --- PAGES ---
if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    st.subheader("📋 Matières")
    for m in st.session_state.dossiers[choix_dos]: st.info(m)
    st.subheader("⚠️ Alertes Rattrapage")
    st.dataframe(df[(df['Note'] > 0) & (df['Note'] < 10)], use_container_width=True)

elif page == "Planning & Saisie":
    st.title("🗓️ Planning & Saisie")
    
    # Expander repliable pour l'ajout
    with st.expander("➕ Ajouter un chapitre (Cliquer pour ouvrir)"):
        with st.form("Add"):
            mat = st.selectbox("Matière", st.session_state.dossiers[choix_dos])
            nom = st.text_input("Chapitre")
            d0 = st.date_input("Date")
            if st.form_submit_button("Lancer"):
                st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([{'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': nom, 'Date': d0, 'Note': 0}])])
                st.rerun()

    st.subheader("📋 Planning Hebdomadaire")
    # Tableau structuré
    hebdo = df[(df['Date'] >= dt.date.today()) & (df['Date'] <= dt.date.today() + dt.timedelta(days=7))]
    st.table(hebdo[['Date', 'Matiere', 'Chapitre', 'Note']])

    st.markdown("---")
    st.subheader("✏️ Saisie des Notes")
    if not df.empty:
        id_l = st.number_input("Entrer l'index de la ligne (voir tableau ci-dessus)", 0, len(df)-1)
        note = st.slider("Note", 0, 20)
        if st.button("Valider la note"):
            st.session_state.data.loc[df.index[id_l], 'Note'] = note
            st.rerun()

elif page == "Graphiques":
    st.title("📊 Évolution")
    for m in st.session_state.dossiers[choix_dos]:
        st.subheader(f"Matière : {m}")
        m_df = df[df['Matiere'] == m]
        if not m_df.empty: st.line_chart(m_df.set_index('Date')['Note'])