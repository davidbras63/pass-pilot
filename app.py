import streamlit as st
import pandas as pd
import datetime as dt

st.set_page_config(page_title="Pilot Expert Pro", layout="wide")

# --- INITIALISATION TOTALE (Remise à plat) ---
# On réinitialise tout pour supprimer les clés corrompues
if 'reset' not in st.session_state:
    st.session_state.dossiers = {"PASS": ["UE1", "UE2"]}
    st.session_state.data = pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'Type', 'Date', 'Note'])
    st.session_state.config = {
        'cours_max': 5, 
        'seuils': {1: 10, 3: 12, 7: 14}
    }
    st.session_state.intervalles = [1, 3, 7, 14, 30, 60, 90]
    st.session_state.reset = True

# --- SIDEBAR ---
st.sidebar.title("⚙️ Pilot Expert")

with st.sidebar.expander("🛠️ Paramètres"):
    st.session_state.config['cours_max'] = st.number_input("Max cours/jour", 1, 20, st.session_state.config['cours_max'])
    st.write("**Seuils (Note min)**")
    # Utilisation de clés entières pour les seuils
    for j in [1, 3, 7]:
        st.session_state.config['seuils'][j] = st.slider(f"Seuil J{j}", 0, 20, st.session_state.config['seuils'][j])

# Gestion Dossiers
new_dos = st.sidebar.text_input("Créer Dossier")
if st.sidebar.button("Créer Dossier") and new_dos:
    if new_dos not in st.session_state.dossiers:
        st.session_state.dossiers[new_dos] = []
        st.rerun()

choix_dos = st.sidebar.selectbox("Choisir Dossier", list(st.session_state.dossiers.keys()))

new_mat = st.sidebar.text_input("Ajouter Matière", key="new_mat")
if st.sidebar.button("Ajouter Matière") and new_mat:
    st.session_state.dossiers[choix_dos].append(new_mat)
    st.rerun()

st.sidebar.write("---")
page = st.sidebar.radio("Navigation", ["Dashboard", "Planning Hebdo & Saisie"])

# --- LOGIQUE ---
df = st.session_state.data[st.session_state.data['Dossier'] == choix_dos]

if page == "Dashboard":
    st.title(f"🎯 Pilotage : {choix_dos}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Matières", len(st.session_state.dossiers[choix_dos]))
    c2.metric("Chapitres", len(df))
    c3.metric("Moyenne", f"{df[df['Note']>0]['Note'].mean():.1f}/20" if not df[df['Note']>0].empty else "0/20")
    
    st.subheader("📁 Matières")
    for mat in st.session_state.dossiers[choix_dos]:
        col1, col2 = st.columns([4, 1])
        col1.info(f"📘 {mat}")
        if col2.button("Suppr", key=f"del_{mat}"):
            st.session_state.dossiers[choix_dos].remove(mat)
            st.rerun()

elif page == "Planning Hebdo & Saisie":
    st.title("🗓️ Planning Hebdo")
    with st.expander("➕ Ajouter chapitre (Cycle DJ complet)"):
        with st.form("Add", clear_on_submit=True):
            mat = st.selectbox("Matière", st.session_state.dossiers[choix_dos])
            nom = st.text_input("Nom")
            d0 = st.date_input("Date")
            if st.form_submit_button("Lancer"):
                for delta in st.session_state.intervalles:
                    new_row = pd.DataFrame([{'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': nom, 'Type': f"J{delta}", 'Date': d0 + dt.timedelta(days=delta), 'Note': 0}])
                    st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
                st.rerun()

    st.subheader("📋 Planning 7j")
    today = dt.date.today()
    planning_hebdo = df[(df['Date'] >= today) & (df['Date'] <= today + dt.timedelta(days=7))].sort_values('Date')
    st.dataframe(planning_hebdo, use_container_width=True)
    
    if not planning_hebdo.empty:
        idx = st.number_input("ID Ligne", 0, len(planning_hebdo)-1)
        note = st.slider("Note", 0, 20, 10)
        if st.button("Valider"):
            sel_date = planning_hebdo.iloc[idx]['Date']
            sel_chap = planning_hebdo.iloc[idx]['Chapitre']
            st.session_state.data.loc[(st.session_state.data['Date']==sel_date) & (st.session_state.data['Chapitre']==sel_chap), 'Note'] = note
            st.rerun()
