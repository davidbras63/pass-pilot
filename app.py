import streamlit as st
import pandas as pd
import datetime as dt

st.set_page_config(layout="wide")

# --- INITIALISATION ---
if 'dossiers' not in st.session_state:
    st.session_state.dossiers = {"PASS": ["UE1", "UE2"]}
    st.session_state.data = pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note'])
    st.session_state.config = {'cours_max': 5, 'cadencier': [1, 3, 7, 14, 30], 'seuils': {1: 10, 3: 12, 7: 14, 14: 15, 30: 16}}

# --- SIDEBAR : RÉGLAGES ---
st.sidebar.title("⚙️ Pilot Expert")
with st.sidebar.expander("🛠️ Réglages complets"):
    st.session_state.config['cours_max'] = st.number_input("Max cours/jour", 1, 20, st.session_state.config['cours_max'])
    cad_str = st.text_input("Cadencier", ",".join(map(str, st.session_state.config['cadencier'])))
    st.session_state.config['cadencier'] = [int(x.strip()) for x in cad_str.split(",")]
    st.write("**Seuils de rattrapage**")
    for j in st.session_state.config['cadencier']:
        st.session_state.config['seuils'][j] = st.slider(f"Seuil J{j}", 0, 20, st.session_state.config['seuils'].get(j, 10))

# Création Dossiers / Matières
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
    st.subheader("Matières suivies")
    for m in st.session_state.dossiers[choix_dos]:
        col1, col2 = st.columns([4, 1])
        col1.info(f"{m} : {len(df[df['Matiere'] == m])} sessions planifiées")
        if col2.button("🗑️", key=f"del_{m}"):
            st.session_state.dossiers[choix_dos].remove(m)
            st.rerun()
    st.subheader("⚠️ Alertes Rattrapage")
    st.dataframe(df[(df['Note'] > 0) & (df['Note'] < 10)], use_container_width=True)

elif page == "Planning & Saisie":
    st.title("🗓️ Planning & Saisie")
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
    
    st.markdown("---")
    st.subheader("✏️ Saisie des Notes")
    # Insertion de la colonne ID au début pour le tableau
    df_display = st.session_state.data.copy()
    df_display.insert(0, 'ID', df_display.index)
    st.dataframe(df_display, use_container_width=True)
    
    # Saisie simple
    id_s = st.number_input("Entrez l'ID du chapitre", 0, len(st.session_state.data)-1 if not st.session_state.data.empty else 0)
    note = st.number_input("Note", 0, 20)
    if st.button("Valider la note"):
        st.session_state.data.loc[id_s, 'Note'] = note
        st.rerun()

elif page == "Graphiques":
    st.title("📊 Progression par Chapitre")
    if not df.empty:
        stats = df[df['Note'] > 0].groupby('Chapitre')['Note'].mean()
        st.bar_chart(stats)
