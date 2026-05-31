import streamlit as st
import pandas as pd
import datetime as dt

st.set_page_config(page_title="Pilot Expert Pro", layout="wide")

# --- INITIALISATION SÉCURISÉE (Évite les erreurs de colonnes) ---
colonnes_requises = ['Dossier', 'Matiere', 'Chapitre', 'Type', 'Date', 'Note']

if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=colonnes_requises)
else:
    # Si des colonnes manquent, on les ajoute pour réparer l'ancienne base
    for col in colonnes_requises:
        if col not in st.session_state.data.columns:
            st.session_state.data[col] = None

if 'dossiers' not in st.session_state:
    st.session_state.dossiers = {"PASS": ["UE1", "UE2"]}
    st.session_state.config = {'cours_max': 5, 'seuils': {1: 10, 3: 12, 7: 14}}
    st.session_state.intervalles = [1, 3, 7, 14, 30, 60, 90]

# --- SIDEBAR : RÉGLAGES & DOSSIERS ---
st.sidebar.title("⚙️ Pilot Expert")

with st.sidebar.expander("🛠️ Paramètres & Seuils"):
    st.session_state.config['cours_max'] = st.number_input("Max cours/jour", 1, 20, st.session_state.config['cours_max'])
    st.write("---")
    st.write("**Seuils (Note min)**")
    for j in [1, 3, 7]:
        st.session_state.config['seuils'][j] = st.slider(f"Seuil J{j}", 0, 20, st.session_state.config['seuils'][j])

st.sidebar.write("---")
new_dos = st.sidebar.text_input("Ajouter Dossier (ex: BAC)")
if st.sidebar.button("Créer Dossier") and new_dos:
    if new_dos not in st.session_state.dossiers:
        st.session_state.dossiers[new_dos] = []
        st.rerun()

choix_dos = st.sidebar.selectbox("Choisir Dossier", list(st.session_state.dossiers.keys()))

new_mat = st.sidebar.text_input("Ajouter Matière", key="new_mat")
if st.sidebar.button("Ajouter Matière") and new_mat:
    st.session_state.dossiers[choix_dos].append(new_mat)
    st.rerun()

# --- NAVIGATION ---
page = st.sidebar.radio("Navigation", ["Dashboard", "Planning Hebdo & Saisie"])

# --- LOGIQUE ---
df = st.session_state.data[st.session_state.data['Dossier'] == choix_dos]

if page == "Dashboard":
    st.title(f"🎯 Pilotage : {choix_dos}")
    # Métriques
    c1, c2, c3 = st.columns(3)
    c1.metric("Matières", len(st.session_state.dossiers[choix_dos]))
    c2.metric("Chapitres totaux", len(st.session_state.data['Chapitre'].unique()))
    c3.metric("Moyenne", f"{df[df['Note']>0]['Note'].mean():.1f}/20" if not df[df['Note']>0].empty else "0/20")
    
    st.subheader("⚠️ Alertes Rattrapage")
    # Affiche les chapitres sous le seuil
    alertes = df[(df['Note'] > 0) & (df['Note'] < 10)]
    st.dataframe(alertes, use_container_width=True)

elif page == "Planning Hebdo & Saisie":
    st.title("🗓️ Planning Hebdomadaire & Saisie")
    
    with st.expander("➕ Ajouter un chapitre (Génère tout le cycle DJ)"):
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
        st.dataframe(planning_hebdo, use_container_width=True)
        st.subheader("✏️ Saisie des Notes")
        idx = st.number_input("ID Ligne (voir tableau)", 0, len(planning_hebdo)-1)
        note = st.slider("Note", 0, 20, 10)
        if st.button("Valider la note"):
            sel_date = planning_hebdo.iloc[idx]['Date']
            sel_chap = planning_hebdo.iloc[idx]['Chapitre']
            st.session_state.data.loc[(st.session_state.data['Date']==sel_date) & (st.session_state.data['Chapitre']==sel_chap), 'Note'] = note
            st.rerun()
    else:
        st.info("Aucun rappel prévu cette semaine.")