import streamlit as st
import pandas as pd
import datetime as dt

st.set_page_config(layout="wide")

# --- INITIALISATION ---
if 'dossiers' not in st.session_state:
    st.session_state.dossiers = {"PASS": ["UE1", "UE2"]}
    st.session_state.data = pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note'])
    st.session_state.config = {'cours_max': 5, 'cadencier': [1, 3, 7, 14, 30]}

# --- SIDEBAR ---
st.sidebar.title("⚙️ Pilot Expert")
with st.sidebar.expander("🛠️ Réglages"):
    st.session_state.config['cours_max'] = st.number_input("Max cours/jour", 1, 20, st.session_state.config['cours_max'])

choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.dossiers.keys()))

new_mat = st.sidebar.text_input("Nouvelle Matière")
if st.sidebar.button("Ajouter Matière") and new_mat: 
    st.session_state.dossiers[choix_dos].append(new_mat)
    st.rerun()

# --- PAGES ---
page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])

# --- LOGIQUE ---
df = st.session_state.data[st.session_state.data['Dossier'] == choix_dos]

if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    for m in st.session_state.dossiers[choix_dos]:
        col1, col2 = st.columns([4, 1])
        col1.info(f"{m} : {len(df[df['Matiere'] == m])} sessions")
        if col2.button("🗑️", key=f"del_{m}"):
            st.session_state.dossiers[choix_dos].remove(m)
            st.rerun()

elif page == "Planning & Saisie":
    st.title("🗓️ Planning & Saisie")
    
    # 1. Saisie de notes rapide (ID + Notes virgules)
    st.subheader("✏️ Saisie rapide")
    cols = st.columns([1, 4])
    with cols[0]:
        target_id = st.number_input("ID à modifier", 0, len(st.session_state.data)-1 if not st.session_state.data.empty else 0)
    with cols[1]:
        notes_input = st.text_input("Saisir notes (ex: 12, 14, 16)")
        if st.button("Valider les notes"):
            # On prend la dernière note saisie pour l'affichage, ou on moyenne
            notes_list = [float(n.strip()) for n in notes_input.split(",")]
            st.session_state.data.loc[target_id, 'Note'] = notes_list[-1] 
            st.rerun()

    # 2. Tableau structuré
    st.subheader("Planning détaillé")
    # Ajout d'une colonne ID virtuelle pour l'affichage
    df_display = st.session_state.data.copy()
    df_display.insert(0, 'ID', df_display.index)
    st.dataframe(df_display, use_container_width=True)

    with st.expander("➕ Ajouter un chapitre"):
        with st.form("Add"):
            mat = st.selectbox("Matière", st.session_state.dossiers[choix_dos])
            chap = st.text_input("Nom du Chapitre")
            d0 = st.date_input("Date J0")
            if st.form_submit_button("Générer"):
                for j in [0] + st.session_state.config['cadencier']:
                    new_row = {'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 
                               'J_Type': f"J{j}", 'Date': d0 + dt.timedelta(days=j), 'Note': 0}
                    st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=True)
                st.rerun()

elif page == "Graphiques":
    st.title("📊 Progression")
    if not df.empty:
        stats = df[df['Note'] > 0].groupby('Chapitre')['Note'].mean()
        st.bar_chart(stats)