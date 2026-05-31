import streamlit as st
import pandas as pd
import datetime as dt

st.set_page_config(page_title="Pilot Expert Pro", layout="wide")

# --- INITIALISATION ---
if 'dossiers' not in st.session_state:
    st.session_state.dossiers = {"PASS": ["UE1", "UE2"]}
    st.session_state.data = pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'Type', 'Date', 'Note'])
    # Intervalles complets de la méthode DJ
    st.session_state.intervalles = [1, 3, 7, 14, 30, 60, 90]

# --- SIDEBAR ---
st.sidebar.title("⚙️ Pilot Expert")

# Gestion Dossiers
new_dos = st.sidebar.text_input("Créer Dossier (ex: BAC)")
if st.sidebar.button("Créer Dossier") and new_dos:
    if new_dos not in st.session_state.dossiers:
        st.session_state.dossiers[new_dos] = []
        st.rerun()

choix_dos = st.sidebar.selectbox("Choisir Dossier", list(st.session_state.dossiers.keys()))

# Gestion Matières
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
    c2.metric("Chapitres en cours", len(df['Chapitre'].unique()))
    c3.metric("Moyenne", f"{df[df['Note']>0]['Note'].mean():.1f}/20" if not df[df['Note']>0].empty else "0/20")
    
    st.subheader("📁 Matières créées")
    for mat in st.session_state.dossiers[choix_dos]:
        col1, col2 = st.columns([4, 1])
        col1.info(f"📘 {mat}")
        if col2.button(f"Supprimer", key=f"del_{mat}"):
            st.session_state.dossiers[choix_dos].remove(mat)
            st.session_state.data = st.session_state.data[st.session_state.data['Matiere'] != mat]
            st.rerun()

elif page == "Planning Hebdo & Saisie":
    st.title("🗓️ Planning Hebdomadaire")
    
    with st.expander("➕ Ajouter un chapitre (Génère tout le planning DJ)"):
        with st.form("Add", clear_on_submit=True):
            mat = st.selectbox("Matière", st.session_state.dossiers[choix_dos] if st.session_state.dossiers[choix_dos] else ["Aucune"])
            nom = st.text_input("Nom du Chapitre")
            d0 = st.date_input("Date de début")
            if st.form_submit_button("Lancer Planning"):
                for delta in st.session_state.intervalles:
                    new_row = pd.DataFrame([{
                        'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': nom, 
                        'Type': f"J{delta}", 'Date': d0 + dt.timedelta(days=delta), 'Note': 0
                    }])
                    st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
                st.rerun()

    st.subheader("📋 Planning des 7 prochains jours")
    today = dt.date.today()
    next_week = today + dt.timedelta(days=7)
    planning_hebdo = df[(df['Date'] >= today) & (df['Date'] <= next_week)].sort_values('Date')
    
    if not planning_hebdo.empty:
        st.dataframe(planning_hebdo.reset_index(drop=True), use_container_width=True)
        
        st.subheader("✏️ Saisie des Notes")
        idx = st.number_input("ID ligne (voir tableau ci-dessus)", 0, len(planning_hebdo)-1)
        note = st.slider("Note", 0, 20, 10)
        if st.button("Valider la note"):
            # On cherche la ligne exacte par Date et Chapitre
            sel_date = planning_hebdo.iloc[idx]['Date']
            sel_chap = planning_hebdo.iloc[idx]['Chapitre']
            st.session_state.data.loc[(st.session_state.data['Date']==sel_date) & (st.session_state.data['Chapitre']==sel_chap), 'Note'] = note
            st.rerun()
    else:
        st.info("Aucun rappel prévu pour les 7 prochains jours.")