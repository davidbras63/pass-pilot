import streamlit as st
import pandas as pd

st.set_page_config(page_title="Pilot Expert Pro", layout="wide")

# --- INITIALISATION SÉCURISÉE ---
if 'dossiers' not in st.session_state or not isinstance(st.session_state.dossiers, dict):
    st.session_state.dossiers = {"PASS": ["UE1", "UE2"]}
    st.session_state.data = pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'Note'])
    st.session_state.config = {'cours_max': 5, 'J1': 1}

# --- SIDEBAR ---
st.sidebar.title("⚙️ Pilot Expert")
with st.sidebar.expander("🛠️ Paramètres"):
    st.session_state.config['cours_max'] = st.number_input("Max cours/jour", 1, 20, st.session_state.config['cours_max'])

st.sidebar.write("---")
new_dos = st.sidebar.text_input("Ajouter Dossier")
if st.sidebar.button("Créer Dossier") and new_dos:
    if new_dos not in st.session_state.dossiers:
        st.session_state.dossiers[new_dos] = []
        st.rerun()

choix_dos = st.sidebar.selectbox("Choisir Dossier", list(st.session_state.dossiers.keys()), key="select_dossier")

new_mat = st.sidebar.text_input("Ajouter Matière dans " + choix_dos)
if st.sidebar.button("Ajouter Matière") and new_mat:
    st.session_state.dossiers[choix_dos].append(new_mat)
    st.rerun()

# --- NAVIGATION ---
page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Notes", "Suivi Graphique"])

# --- LOGIQUE ---
df = st.session_state.data[st.session_state.data['Dossier'] == choix_dos]

if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    
    # Métriques
    c1, c2, c3 = st.columns(3)
    c1.metric("Matières", len(st.session_state.dossiers[choix_dos]))
    c2.metric("Chapitres", len(df))
    c3.metric("Moyenne", f"{df[df['Note']>0]['Note'].mean():.1f}/20" if not df[df['Note']>0].empty else "0/20")
    
    st.write("---")
    st.subheader("📁 Gérer les Matières")
    # Affichage des matières avec bouton de suppression
    for mat in st.session_state.dossiers[choix_dos]:
        col1, col2 = st.columns([4, 1])
        col1.write(f"📘 **{mat}**")
        if col2.button(f"Supprimer {mat}", key=f"del_{mat}"):
            st.session_state.dossiers[choix_dos].remove(mat)
            # Optionnel : supprimer aussi les données associées
            st.session_state.data = st.session_state.data[st.session_state.data['Matiere'] != mat]
            st.rerun()
    
    st.subheader("📋 État global des chapitres")
    st.dataframe(df, use_container_width=True)

elif page == "Planning & Notes":
    st.title(f"🗓️ Planning - {choix_dos}")
    with st.form("Ajout_Chapitre"):
        mats = st.session_state.dossiers[choix_dos]
        mat = st.selectbox("Sélectionner la Matière", mats if mats else ["Aucune"])
        nom = st.text_input("Nom du Chapitre")
        if st.form_submit_button("Ajouter") and mat != "Aucune":
            new_row = pd.DataFrame([{'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': nom, 'Note': 0}])
            st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
            st.rerun()
    
    if not df.empty:
        idx = st.number_input("ID Ligne", 0, len(df)-1)
        note = st.number_input("Note", 0, 20)
        if st.button("Valider"):
            st.session_state.data.loc[df.index[idx], 'Note'] = note
            st.rerun()
        st.dataframe(df, use_container_width=True)

elif page == "Suivi Graphique":
    st.title(f"📊 {choix_dos} - Détail")
    for m in st.session_state.dossiers[choix_dos]:
        st.subheader(f"Matière : {m}")
        sub = df[df['Matiere'] == m]
        if not sub.empty: st.line_chart(sub['Note'])
        else: st.info(f"Aucune note pour {m}")