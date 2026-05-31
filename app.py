import streamlit as st
import pandas as pd
import datetime as dt

st.set_page_config(page_title="Pilot Universel", layout="wide")

# --- INITIALISATION ---
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'Type', 'Date', 'Note'])
if 'dossiers' not in st.session_state:
    st.session_state.dossiers = ["PASS"]

# --- BARRE LATÉRALE : Gestion des dossiers ---
st.sidebar.title("📁 Mes Dossiers")
new_dossier = st.sidebar.text_input("Créer un nouveau dossier (ex: BAC)")
if st.sidebar.button("Ajouter dossier") and new_dossier:
    if new_dossier not in st.session_state.dossiers:
        st.session_state.dossiers.append(new_dossier)
        st.rerun()

choix_dossier = st.sidebar.selectbox("Sélectionner un dossier", st.session_state.dossiers)

# --- NAVIGATION DANS LE DOSSIER ---
st.sidebar.write("---")
st.sidebar.header(f"Espace {choix_dossier}")
page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Matières", "Saisie Notes"])

# --- FILTRAGE DONNÉES ---
df = st.session_state.data[st.session_state.data['Dossier'] == choix_dossier]

# --- PAGES ---
if page == "Dashboard":
    st.title(f"🎯 Dashboard - {choix_dossier}")
    if not df.empty:
        c1, c2 = st.columns(2)
        c1.metric("Chapitres suivis", len(df['Chapitre'].unique()))
        c2.metric("Note moyenne", f"{df[df['Note']>0]['Note'].mean():.1f}/20" if not df[df['Note']>0].empty else "N/A")
        st.line_chart(df.groupby('Date')['Note'].mean())
    else:
        st.info("Aucune donnée pour ce dossier.")

elif page == "Planning & Matières":
    st.title("🗓️ Planning")
    with st.expander("➕ Ajouter un élément"):
        with st.form("Ajout"):
            mat = st.text_input("Matière (ex: Anatomie)")
            nom = st.text_input("Chapitre")
            d0 = st.date_input("Date")
            if st.form_submit_button("Ajouter au planning"):
                new_row = pd.DataFrame([{'Dossier': choix_dossier, 'Matiere': mat, 'Chapitre': nom, 'Type': 'Révision', 'Date': d0, 'Note': 0}])
                st.session_state.data = pd.concat([st.session_state.data, new_row])
                st.rerun()
    st.dataframe(df, use_container_width=True)

elif page == "Saisie Notes":
    st.title("✏️ Saisir Notes")
    if not df.empty:
        idx = st.number_input("ID Ligne (voir tableau Planning)", 0, len(df)-1)
        note = st.number_input("Note obtenue", 0, 20)
        if st.button("Valider la note"):
            st.session_state.data.loc[df.index[idx], 'Note'] = note
            st.rerun()
    else:
        st.info("Ajoutez des chapitres dans l'onglet 'Planning' pour saisir des notes.")