import streamlit as st
import pandas as pd
import datetime as dt

st.set_page_config(page_title="Pilot Universel", layout="wide")

# --- INITIALISATION ---
colonnes = ['Dossier', 'Matiere', 'Chapitre', 'Date', 'Note']
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=colonnes)
if 'dossiers' not in st.session_state:
    st.session_state.dossiers = ["PASS"]

# --- SIDEBAR ---
st.sidebar.title("📁 Mes Dossiers")
new_dossier = st.sidebar.text_input("Créer un dossier")
if st.sidebar.button("Ajouter") and new_dossier and new_dossier not in st.session_state.dossiers:
    st.session_state.dossiers.append(new_dossier)
    st.rerun()

choix_dossier = st.sidebar.selectbox("Sélectionner un dossier", st.session_state.dossiers)
st.sidebar.write("---")
page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphes par Matière"])

# --- LOGIQUE ---
df = st.session_state.data[st.session_state.data['Dossier'] == choix_dossier]

if page == "Dashboard":
    st.title(f"🎯 Dashboard - {choix_dossier}")
    if not df.empty:
        c1, c2 = st.columns(2)
        c1.metric("Chapitres", len(df['Chapitre'].unique()))
        c2.metric("Moyenne", f"{df[df['Note']>0]['Note'].mean():.1f}/20" if not df[df['Note']>0].empty else "N/A")
    else:
        st.info("Ajoutez des données dans Planning & Saisie.")

elif page == "Planning & Saisie":
    st.title(f"🗓️ Planning - {choix_dossier}")
    with st.expander("➕ Ajouter un chapitre"):
        with st.form("Ajout"):
            mat = st.text_input("Matière (ex: UE1, Math)")
            nom = st.text_input("Nom du Chapitre")
            d0 = st.date_input("Date")
            if st.form_submit_button("Ajouter"):
                new_row = pd.DataFrame([{'Dossier': choix_dossier, 'Matiere': mat, 'Chapitre': nom, 'Date': d0, 'Note': 0}])
                st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
                st.rerun()
    
    st.subheader("📋 Liste & Saisie")
    if not df.empty:
        # Affichage du tableau pour voir les ID
        st.dataframe(df.reset_index(), use_container_width=True)
        # Saisie de note
        idx_input = st.number_input("ID Ligne (colonne index)", 0, len(df)-1)
        note_input = st.number_input("Note (0-20)", 0, 20)
        if st.button("Valider la note"):
            st.session_state.data.loc[df.index[idx_input], 'Note'] = note_input
            st.rerun()
    else:
        st.info("Aucun chapitre dans ce dossier.")

elif page == "Graphes par Matière":
    st.title(f"📊 Suivi par Matière - {choix_dossier}")
    if not df.empty:
        for mat in df['Matiere'].unique():
            st.subheader(f"Matière : {mat}")
            sub = df[df['Matiere'] == mat]
            st.line_chart(sub.set_index('Date')['Note'])
    else:
        st.info("Aucune donnée.")