import streamlit as st
import pandas as pd
import datetime as dt

st.set_page_config(layout="wide")

# --- INITIALISATION ---
if 'init' not in st.session_state:
    st.session_state.dossiers = {"PASS": ["UE1", "UE2"]}
    st.session_state.data = pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'Date', 'Note'])
    st.session_state.config = {'cours_max': 5, 'cadencier': [1, 3, 7, 14, 30], 'seuils': {1: 10, 3: 12, 7: 14, 14: 15, 30: 16}}
    st.session_state.init = True

# --- SIDEBAR : RÉGLAGES ---
st.sidebar.title("⚙️ Pilot Expert")
with st.sidebar.expander("🛠️ Réglages complets"):
    st.session_state.config['cours_max'] = st.number_input("Max cours/jour", 1, 20, st.session_state.config['cours_max'])
    cad_str = st.text_input("Jours du cadencier", ",".join(map(str, st.session_state.config['cadencier'])))
    st.session_state.config['cadencier'] = [int(x.strip()) for x in cad_str.split(",")]
    st.write("**Seuils de rattrapage**")
    for j in st.session_state.config['cadencier']:
        st.session_state.config['seuils'][j] = st.slider(f"Seuil J{j}", 0, 20, st.session_state.config['seuils'].get(j, 10))

# Gestion Dossiers / Matières
new_dos = st.sidebar.text_input("Créer Dossier")
if st.sidebar.button("Ajouter Dossier") and new_dos: st.session_state.dossiers[new_dos] = []
choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.dossiers.keys()))

new_mat = st.sidebar.text_input("Ajouter Matière")
if st.sidebar.button("Ajouter Matière") and new_mat: st.session_state.dossiers[choix_dos].append(new_mat)

page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])

# --- LOGIQUE ---
df = st.session_state.data[st.session_state.data['Dossier'] == choix_dos]

# --- PAGES ---
if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    st.subheader("État des matières")
    for m in st.session_state.dossiers[choix_dos]:
        nb = len(df[df['Matiere'] == m])
        st.write(f"**{m}** : {nb} chapitres réalisés")
    st.subheader("⚠️ Alertes Rattrapage")
    st.dataframe(df[(df['Note'] > 0) & (df['Note'] < 10)], use_container_width=True)

elif page == "Planning & Saisie":
    st.title("🗓️ Planning & Saisie")
    with st.expander("➕ Ajouter un chapitre"):
        with st.form("Add"):
            mat = st.selectbox("Matière", st.session_state.dossiers[choix_dos])
            nom = st.text_input("Chapitre")
            d0 = st.date_input("Date")
            if st.form_submit_button("Ajouter"):
                new_row = pd.DataFrame([{'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': nom, 'Date': d0, 'Note': 0}])
                st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
                st.rerun()

    # Planning Hebdo
    cols = st.columns(7)
    for i, day in enumerate([dt.date.today() + dt.timedelta(days=i) for i in range(7)]):
        with cols[i]:
            st.markdown(f"**{day.strftime('%A %d')}**")
            for idx, r in df[df['Date'] == day].iterrows():
                st.write(f"ID {idx}: {r['Matiere']} ({r['Chapitre']})")

    st.subheader("✏️ Saisie Notes (Saisir ID ligne)")
    id_saisie = st.number_input("ID Chapitre", 0, len(st.session_state.data)-1 if not st.session_state.data.empty else 0)
    
    # Affichage dynamique du chapitre sélectionné
    if not st.session_state.data.empty and id_saisie in st.session_state.data.index:
        chap_info = st.session_state.data.loc[id_saisie]
        st.info(f"Vous modifiez : {chap_info['Matiere']} - {chap_info['Chapitre']}")
        note = st.number_input("Note", 0, 20)
        if st.button("Enregistrer Note"):
            st.session_state.data.loc[id_saisie, 'Note'] = note
            st.rerun()

    st.dataframe(df, use_container_width=True)

elif page == "Graphiques":
    st.title("📊 Évolution")
    for m in st.session_state.dossiers[choix_dos]:
        st.subheader(m)
        m_df = df[df['Matiere'] == m]
        if not m_df.empty: st.line_chart(m_df.set_index('Date')['Note'])