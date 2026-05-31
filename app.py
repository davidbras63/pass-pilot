import streamlit as st
import pandas as pd
import datetime as dt

st.set_page_config(page_title="Pilot Expert Pro", layout="wide")

# --- INITIALISATION ---
if 'dossiers' not in st.session_state:
    st.session_state.dossiers = {"PASS": ["UE1", "UE2"]}
    st.session_state.data = pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'Date', 'Note'])
    st.session_state.cadencier = [1, 3, 7, 14, 30, 60, 90]
    st.session_state.seuil = 10

# --- SIDEBAR ---
st.sidebar.title("⚙️ Pilot Expert Pro")

with st.sidebar.expander("🛠️ Réglages"):
    cad_input = st.text_input("Cadencier (jours)", ",".join(map(str, st.session_state.cadencier)))
    st.session_state.cadencier = [int(x.strip()) for x in cad_input.split(",")]
    st.session_state.seuil = st.number_input("Seuil de rattrapage", 0, 20, st.session_state.seuil)

# Gestion Dossiers
new_dos = st.sidebar.text_input("Ajouter Dossier")
if st.sidebar.button("Créer Dossier") and new_dos:
    st.session_state.dossiers[new_dos] = []
    st.rerun()

choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.dossiers.keys()))

# Gestion Matières
new_mat = st.sidebar.text_input("Ajouter Matière")
if st.sidebar.button("Ajouter Matière") and new_mat:
    st.session_state.dossiers[choix_dos].append(new_mat)
    st.rerun()

page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Suivi Graphique"])

# --- LOGIQUE ---
df = st.session_state.data[st.session_state.data['Dossier'] == choix_dos]

# --- PAGES ---
if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    cols = st.columns(3)
    cols[0].metric("Matières", len(st.session_state.dossiers[choix_dos]))
    cols[1].metric("Moyenne", f"{df[df['Note']>0]['Note'].mean():.1f}/20")
    
    st.subheader("⚠️ Alertes Rattrapage (Note < seuil)")
    st.dataframe(df[(df['Note'] > 0) & (df['Note'] < st.session_state.seuil)], use_container_width=True)

elif page == "Planning & Saisie":
    st.title("🗓️ Planning Hebdomadaire & Notes")
    
    with st.expander("➕ Ajouter un chapitre"):
        with st.form("Add"):
            mat = st.selectbox("Matière", st.session_state.dossiers[choix_dos])
            nom = st.text_input("Chapitre")
            d0 = st.date_input("Date")
            if st.form_submit_button("Ajouter"):
                st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([{'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': nom, 'Date': d0, 'Note': 0}])])
                st.rerun()
    
    # Planning Visuel
    cols = st.columns(7)
    today = dt.date.today()
    for i in range(7):
        jour = today + dt.timedelta(days=i)
        with cols[i]:
            st.markdown(f"**{jour.strftime('%A %d')}**")
            for idx, row in df[df['Date'] == jour].iterrows():
                st.info(f"{row['Matiere']}: {row['Chapitre']} (Note: {row['Note']})")

    st.subheader("✏️ Saisie des Notes")
    if not df.empty:
        id_l = st.number_input("Entrez l'index de la ligne (voir tableau)", 0, len(df)-1)
        note = st.slider("Note", 0, 20)
        if st.button("Valider la note"):
            st.session_state.data.loc[df.index[id_l], 'Note'] = note
            st.rerun()
        st.dataframe(df, use_container_width=True)

elif page == "Suivi Graphique":
    st.title("📊 Évolution par Matière")
    for m in st.session_state.dossiers[choix_dos]:
        st.subheader(m)
        m_df = df[df['Matiere'] == m]
        if not m_df.empty: st.line_chart(m_df.set_index('Date')['Note'])