import streamlit as st
import pandas as pd
import datetime as dt

st.set_page_config(page_title="Pilot Expert Pro", layout="wide")

# --- INITIALISATION ---
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'Date', 'Note'])
if 'dossiers' not in st.session_state:
    st.session_state.dossiers = {"PASS": ["UE1", "UE2", "UE3"], "BAC": ["Maths", "Anglais"]}
if 'config' not in st.session_state:
    st.session_state.config = {'cours_max': 5, 'J1': 1, 'J3': 3, 'J7': 7}

# --- SIDEBAR : PARAMÈTRES & DOSSIERS ---
st.sidebar.title("⚙️ Pilot Expert")

with st.sidebar.expander("🛠️ Paramètres"):
    st.session_state.config['cours_max'] = st.number_input("Max cours/jour", 1, 20, st.session_state.config['cours_max'])
    st.session_state.config['J1'] = st.number_input("Intervalle J1", 1, 30, st.session_state.config['J1'])

st.sidebar.write("---")
new_dos = st.sidebar.text_input("Créer Dossier (ex: PASS)")
if st.sidebar.button("Ajouter Dossier") and new_dos:
    if new_dos not in st.session_state.dossiers:
        st.session_state.dossiers[new_dos] = []
        st.rerun()

choix_dos = st.sidebar.selectbox("Choisir Dossier", list(st.session_state.dossiers.keys()))

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
    if not df.empty:
        c1, c2 = st.columns(2)
        c1.metric("Matières créées", len(st.session_state.dossiers[choix_dos]))
        c2.metric("Moyenne", f"{df[df['Note']>0]['Note'].mean():.1f}/20")
    st.dataframe(df, use_container_width=True)

elif page == "Planning & Notes":
    st.title(f"🗓️ Planning - {choix_dos}")
    with st.form("Ajout"):
        mat = st.selectbox("Choisir Matière", st.session_state.dossiers[choix_dos])
        nom = st.text_input("Chapitre")
        d0 = st.date_input("Date")
        if st.form_submit_button("Ajouter"):
            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([{'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': nom, 'Date': d0, 'Note': 0}])], ignore_index=True)
            st.rerun()
    
    idx = st.number_input("ID Ligne (voir tableau)", 0, len(df)-1 if not df.empty else 0)
    note = st.number_input("Note", 0, 20)
    if st.button("Valider note"):
        st.session_state.data.loc[df.index[idx], 'Note'] = note
        st.rerun()

elif page == "Suivi Graphique":
    st.title(f"📊 {choix_dos} - Détail")
    for m in st.session_state.dossiers[choix_dos]:
        st.subheader(m)
        sub = df[df['Matiere'] == m]
        if not sub.empty: st.line_chart(sub.set_index('Date')['Note'])