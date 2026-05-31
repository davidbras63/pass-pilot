import streamlit as st
import pandas as pd
import datetime as dt

st.set_page_config(layout="wide")

# --- INITIALISATION ROBUSTE ---
if 'init_ok' not in st.session_state:
    st.session_state.dossiers = {"PASS": ["UE1", "UE2"]}
    st.session_state.data = pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'Date', 'Note'])
    st.session_state.config = {'cours_max': 5, 'cadencier': [1, 3, 7, 14, 30], 'seuils': {1: 10, 3: 12, 7: 14, 14: 15, 30: 16}}
    st.session_state.init_ok = True

# --- SIDEBAR : RÉGLAGES ---
st.sidebar.title("⚙️ Pilot Expert")
with st.sidebar.expander("🛠️ Réglages"):
    st.session_state.config['cours_max'] = st.number_input("Max cours/jour", 1, 20, st.session_state.config['cours_max'])
    cad_str = st.text_input("Jours (ex: 1,3,7,14,30)", ",".join(map(str, st.session_state.config['cadencier'])))
    st.session_state.config['cadencier'] = [int(x.strip()) for x in cad_str.split(",")]
    st.write("**Seuils de rattrapage par J**")
    for j in st.session_state.config['cadencier']:
        if j not in st.session_state.config['seuils']: st.session_state.config['seuils'][j] = 10
        st.session_state.config['seuils'][j] = st.slider(f"Seuil J{j}", 0, 20, st.session_state.config['seuils'][j])

choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.dossiers.keys()))
new_mat = st.sidebar.text_input("Nouvelle matière")
if st.sidebar.button("Ajouter Matière") and new_mat:
    st.session_state.dossiers[choix_dos].append(new_mat)
    st.rerun()

page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])

# --- LOGIQUE ---
df = st.session_state.data[st.session_state.data['Dossier'] == choix_dos]

# --- PAGES ---
if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    st.subheader("Matières")
    for m in st.session_state.dossiers[choix_dos]:
        col1, col2 = st.columns([4, 1])
        col1.info(m)
        if col2.button("Suppr", key=f"del_{m}"):
            st.session_state.dossiers[choix_dos].remove(m)
            st.rerun()
    st.subheader("⚠️ Alertes Rattrapage")
    st.dataframe(df[(df['Note'] > 0) & (df['Note'] < 10)], use_container_width=True)

elif page == "Planning & Saisie":
    st.title("🗓️ Planning Hebdomadaire")
    with st.expander("➕ Ajouter un chapitre"):
        with st.form("Add"):
            mat = st.selectbox("Matière", st.session_state.dossiers[choix_dos])
            nom = st.text_input("Chapitre")
            d0 = st.date_input("Date")
            if st.form_submit_button("Ajouter"):
                new_row = pd.DataFrame([{'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': nom, 'Date': d0, 'Note': 0}])
                st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
                st.rerun()
    
    cols = st.columns(7)
    today = dt.date.today()
    for i in range(7):
        jour = today + dt.timedelta(days=i)
        with cols[i]:
            st.markdown(f"**{jour.strftime('%A %d')}**")
            for idx, r in df[df['Date'] == jour].iterrows():
                st.write(f"- {r['Matiere']}: {r['Chapitre']}")
    
    st.markdown("---")
    st.subheader("✏️ Saisie des Notes / Suppression Chapitre")
    if not df.empty:
        id_l = st.number_input("ID ligne", 0, len(df)-1)
        note = st.slider("Note", 0, 20)
        col1, col2 = st.columns(2)
        if col1.button("Valider note"):
            st.session_state.data.loc[df.index[id_l], 'Note'] = note
            st.rerun()
        if col2.button("Supprimer chapitre (ID)"):
            st.session_state.data = st.session_state.data.drop(df.index[id_l])
            st.rerun()
        st.dataframe(df, use_container_width=True)

elif page == "Graphiques":
    st.title("📊 Évolution Moyenne")
    for m in st.session_state.dossiers[choix_dos]:
        st.subheader(m)
        m_df = df[df['Matiere'] == m]
        if not m_df.empty: 
            st.line_chart(m_df.set_index('Date')['Note'])
