import streamlit as st
import pandas as pd
import datetime as dt

st.set_page_config(layout="wide")

# --- INITIALISATION ---
if 'dossiers' not in st.session_state:
    st.session_state.dossiers = {"PASS": ["UE1", "UE2"]}
    st.session_state.data = pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note'])
    st.session_state.config = {'cours_max': 5, 'cadencier': [1, 3, 7, 14, 30], 'seuils': {1: 10, 3: 12, 7: 14, 14: 15, 30: 16}}

# --- SIDEBAR ---
st.sidebar.title("⚙️ Pilot Expert")
with st.sidebar.expander("🛠️ Réglages complets"):
    st.session_state.config['cours_max'] = st.number_input("Max cours/jour", 1, 20, st.session_state.config['cours_max'])
    cad_str = st.text_input("Cadencier", ",".join(map(str, st.session_state.config['cadencier'])))
    st.session_state.config['cadencier'] = [int(x.strip()) for x in cad_str.split(",")]

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
    for m in st.session_state.dossiers[choix_dos]:
        col1, col2 = st.columns([4, 1])
        col1.info(f"{m} : {len(df[df['Matiere'] == m])} sessions planifiées")
        if col2.button("🗑️", key=f"del_{m}"):
            st.session_state.dossiers[choix_dos].remove(m)
            st.rerun()
    st.dataframe(df[(df['Note'] > 0) & (df['Note'] < 10)], use_container_width=True)

elif page == "Planning & Saisie":
    st.title("🗓️ Planning Hebdomadaire & Saisie")
    
    # 1. Planning Hebdo visuel
    cols = st.columns(7)
    today = dt.date.today()
    for i in range(7):
        day = today + dt.timedelta(days=i)
        with cols[i]:
            st.markdown(f"**{day.strftime('%A %d')}**")
            for idx, r in df[df['Date'] == day].iterrows():
                st.write(f"ID {idx}: {r['Chapitre']} ({r['J_Type']})")

    # 2. Ajout Chapitre
    with st.expander("➕ Ajouter Chapitre"):
        with st.form("Add"):
            mat = st.selectbox("Matière", st.session_state.dossiers[choix_dos])
            chap = st.text_input("Nom du Chapitre")
            d0 = st.date_input("Date J0")
            if st.form_submit_button("Générer tout le planning"):
                for j in [0] + st.session_state.config['cadencier']:
                    new_row = {'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 
                               'J_Type': f"J{j}", 'Date': d0 + dt.timedelta(days=j), 'Note': 0}
                    st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=True)
                st.rerun()

    # 3. Saisie directe par tableau (Data Editor)
    st.subheader("✏️ Saisie des Notes (Cliquez sur la colonne 'Note')")
    df_with_id = st.session_state.data.copy()
    df_with_id.insert(0, 'ID', df_with_id.index)
    
    # Éditeur interactif
    edited_df = st.data_editor(df_with_id, use_container_width=True)
    
    if st.button("Enregistrer les notes"):
        # On met à jour le dataframe global avec les modifs faites dans l'éditeur
        st.session_state.data = edited_df.drop(columns=['ID'])
        st.rerun()

elif page == "Graphiques":
    st.title("📊 Progression par Chapitre")
    if not df.empty:
        stats = df[df['Note'] > 0].groupby('Chapitre')['Note'].mean()
        st.bar_chart(stats)
