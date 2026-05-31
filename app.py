import streamlit as st
import pandas as pd
import datetime as dt

st.set_page_config(layout="wide")

# --- INITIALISATION ---
if 'dossiers' not in st.session_state:
    st.session_state.dossiers = {"PASS": ["UE1", "UE2"]}
    # 'ID' est créé automatiquement comme index du DataFrame
    st.session_state.data = pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'Date', 'Note'])
    st.session_state.config = {'cours_max': 5, 'cadencier': [1, 3, 7, 14, 30], 'seuils': {1: 10, 3: 12, 7: 14, 14: 15, 30: 16}}

# --- SIDEBAR ---
st.sidebar.title("⚙️ Réglages")
with st.sidebar.expander("🛠️ Configuration"):
    st.session_state.config['cours_max'] = st.number_input("Max cours/jour", 1, 20, st.session_state.config['cours_max'])
    cad_input = st.text_input("Cadencier (jours)", ",".join(map(str, st.session_state.config['cadencier'])))
    st.session_state.config['cadencier'] = [int(x.strip()) for x in cad_input.split(",")]
    for j in st.session_state.config['cadencier']:
        st.session_state.config['seuils'][j] = st.slider(f"Seuil J{j}", 0, 20, st.session_state.config['seuils'].get(j, 10))

# Dossiers et Matières
new_dos = st.sidebar.text_input("Créer Dossier")
if st.sidebar.button("Créer") and new_dos: st.session_state.dossiers[new_dos] = []
choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.dossiers.keys()))

new_mat = st.sidebar.text_input("Ajouter Matière")
if st.sidebar.button("Ajouter") and new_mat: st.session_state.dossiers[choix_dos].append(new_mat)

# --- LOGIQUE ---
df = st.session_state.data[st.session_state.data['Dossier'] == choix_dos]

# --- PAGES ---
page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie"])

if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    for mat in st.session_state.dossiers[choix_dos]:
        nb = len(df[df['Matiere'] == mat])
        st.write(f"**{mat}** : {nb} chapitre(s)")
    st.subheader("⚠️ Alertes Rattrapage")
    st.dataframe(df[(df['Note'] > 0) & (df['Note'] < 10)], use_container_width=True)

elif page == "Planning & Saisie":
    st.title("🗓️ Planning & Saisie")
    
    # 1. Ajout avec affichage de l'ID généré
    with st.expander("➕ Ajouter un chapitre"):
        with st.form("Add"):
            mat = st.selectbox("Matière", st.session_state.dossiers[choix_dos])
            nom = st.text_input("Chapitre")
            d0 = st.date_input("Date")
            if st.form_submit_button("Ajouter"):
                new_row = pd.DataFrame([{'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': nom, 'Date': d0, 'Note': 0}])
                st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
                st.rerun()
    
    # 2. Planning Hebdo (Grille)
    cols = st.columns(7)
    for i, day in enumerate([dt.date.today() + dt.timedelta(days=i) for i in range(7)]):
        with cols[i]:
            st.markdown(f"**{day.strftime('%A %d')}**")
            # Affiche Chapitre + ID pour repérage
            for idx, r in df[df['Date'] == day].iterrows():
                st.write(f"**ID {idx}**: {r['Matiere']} - {r['Chapitre']}")
    
    # 3. Saisie Notes par ID
    st.subheader("✏️ Saisie des Notes")
    id_saisie = st.number_input("Entrez l'ID du chapitre pour saisir la note", 0, len(st.session_state.data)-1 if not st.session_state.data.empty else 0)
    note_saisie = st.number_input("Note (/20)", 0, 20)
    if st.button("Valider la note"):
        st.session_state.data.loc[id_saisie, 'Note'] = note_saisie
        st.rerun()
    
    st.subheader("Tableau de suivi")
    st.dataframe(df, use_container_width=True)
