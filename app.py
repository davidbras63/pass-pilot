import streamlit as st
import pandas as pd
import datetime as dt

st.set_page_config(layout="wide")

# --- INITIALISATION ---
if 'dossiers' not in st.session_state:
    st.session_state.dossiers = {"PASS": ["UE1", "UE2"]}
    st.session_state.data = pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'Date', 'Note'])
    st.session_state.config = {'cours_max': 5, 'cadencier': [1, 3, 7, 14, 30], 'seuils': {1: 10, 3: 12, 7: 14, 14: 15, 30: 16}}

# --- SIDEBAR : RÉGLAGES ---
st.sidebar.title("⚙️ Pilot Expert")
with st.sidebar.expander("🛠️ Réglages (Fixes)"):
    st.session_state.config['cours_max'] = st.number_input("Max cours/jour", 1, 20, st.session_state.config['cours_max'])
    cad_str = st.text_input("Jours", ",".join(map(str, st.session_state.config['cadencier'])))
    st.session_state.config['cadencier'] = [int(x.strip()) for x in cad_str.split(",")]

st.sidebar.divider()
# Gestion Dossiers
new_dos = st.sidebar.text_input("Nouveau Dossier")
if st.sidebar.button("Créer Dossier") and new_dos:
    st.session_state.dossiers[new_dos] = []
    st.rerun()

choix_dos = st.sidebar.selectbox("Sélectionner Dossier", list(st.session_state.dossiers.keys()))

# Gestion Matières du dossier actif
with st.sidebar.expander("Gestion Matières"):
    new_mat = st.text_input("Ajouter Matière")
    if st.button("Ajouter") and new_mat:
        st.session_state.dossiers[choix_dos].append(new_mat)
        st.rerun()
    for m in st.session_state.dossiers[choix_dos]:
        c1, c2 = st.columns([3, 1])
        c1.write(m)
        if c2.button("X", key=f"del_{m}"):
            st.session_state.dossiers[choix_dos].remove(m)
            st.rerun()

page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])

# --- LOGIQUE ---
df = st.session_state.data[st.session_state.data['Dossier'] == choix_dos]

# --- PAGES ---
if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    st.subheader("⚠️ Alertes Rattrapage")
    st.dataframe(df[(df['Note'] > 0) & (df['Note'] < 10)], use_container_width=True)

elif page == "Planning & Saisie":
    st.title("🗓️ Planning & Saisie")
    
    # 1. Planning Hebdo
    st.subheader("Planning de la semaine")
    cols = st.columns(7)
    today = dt.date.today()
    for i in range(7):
        jour = today + dt.timedelta(days=i)
        with cols[i]:
            st.markdown(f"**{jour.strftime('%A %d')}**")
            for _, r in df[df['Date'] == jour].iterrows():
                st.write(f"- {r['Matiere']}: {r['Chapitre']}")

    # 2. Ajout Chapitre
    with st.expander("➕ Ajouter un chapitre"):
        with st.form("Add"):
            mat = st.selectbox("Matière", st.session_state.dossiers[choix_dos])
            nom = st.text_input("Chapitre")
            d0 = st.date_input("Date")
            if st.form_submit_button("Valider"):
                new_row = pd.DataFrame([{'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': nom, 'Date': d0, 'Note': 0}])
                st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
                st.rerun()

    # 3. Saisie Notes
    st.subheader("✏️ Saisie des Notes")
    with st.expander("Voir le tableau des chapitres pour les ID"):
        st.dataframe(df, use_container_width=True)
    
    id_l = st.number_input("Entrer l'ID de la ligne à noter", 0, len(df)-1 if not df.empty else 0)
    note = st.slider("Note", 0, 20)
    if st.button("Valider Note"):
        st.session_state.data.loc[df.index[id_l], 'Note'] = note
        st.rerun()

elif page == "Graphiques":
    st.title("📊 Évolution")
    for m in st.session_state.dossiers[choix_dos]:
        st.subheader(m)
        m_df = df[df['Matiere'] == m]
        if not m_df.empty: st.line_chart(m_df.set_index('Date')['Note'])