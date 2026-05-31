import streamlit as st
import pandas as pd
import datetime as dt
import os

st.set_page_config(layout="wide")

# --- PERSISTANCE ---
DATA_FILE = "data.csv"
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
        if 'ID' not in df.columns: df.insert(0, 'ID', range(len(df)))
        return df
    return pd.DataFrame(columns=['ID', 'Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note'])

def save_data(df): df.to_csv(DATA_FILE, index=False)

if 'data' not in st.session_state: st.session_state.data = load_data()
if 'dossiers' not in st.session_state:
    st.session_state.dossiers = {"PASS": ["UE1", "UE2"]}
    st.session_state.config = {'cours_max': 5, 'cadencier': [1, 3, 7, 14, 30], 'seuils': {1: 10, 3: 12, 7: 14, 14: 15, 30: 16}}

# --- SIDEBAR (Réglages - TOTALEMENT RESTAURÉS) ---
st.sidebar.title("⚙️ Pilot Expert")
with st.sidebar.expander("🛠️ Réglages complets"):
    st.session_state.config['cours_max'] = st.number_input("Max cours/jour", 1, 20, st.session_state.config['cours_max'])
    cad_str = st.text_input("Cadencier", ",".join(map(str, st.session_state.config['cadencier'])))
    st.session_state.config['cadencier'] = [int(x.strip()) for x in cad_str.split(",")]
    for j in st.session_state.config['cadencier']:
        st.session_state.config['seuils'][j] = st.slider(f"Seuil note J{j}", 0, 20, st.session_state.config['seuils'].get(j, 10))

new_dos = st.sidebar.text_input("Créer Dossier")
if st.sidebar.button("Ajouter Dossier") and new_dos: 
    st.session_state.dossiers[new_dos] = []; st.rerun()

choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.dossiers.keys()))
new_mat = st.sidebar.text_input("Ajouter Matière")
if st.sidebar.button("Ajouter Matière") and new_mat: 
    st.session_state.dossiers[choix_dos].append(new_mat); st.rerun()

page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])
df = st.session_state.data[st.session_state.data['Dossier'] == choix_dos].copy()

# --- PAGES (STRUCTURE ORIGINALE RESTAURÉE) ---
if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    # Matières et Poubelles
    for m in st.session_state.dossiers[choix_dos]:
        col1, col2 = st.columns([4, 1])
        col1.info(f"{m} : {len(df[df['Matiere'] == m])} sessions")
        if col2.button("🗑️", key=f"del_{m}"): st.session_state.dossiers[choix_dos].remove(m); st.rerun()
            
    st.subheader("⚠️ Tableau des Rattrapages")
    # Logique rattrapage (seuil)
    rattrapages = df[df['Note'].astype(str).str.split(',').str[-1].astype(float) < 10]
    st.table(rattrapages)
    if st.button("🚀 Placer rattrapages dans les trous (Éviter dimanche)"):
        # Logique de placement automatique intelligent
        for idx, r in rattrapages.iterrows():
            # Chercher jour libre en semaine
            for i in range(1, 15):
                test = dt.date.today() + dt.timedelta(days=i)
                if test.weekday() < 6 and len(df[df['Date'] == test]) < st.session_state.config['cours_max']:
                    st.session_state.data.loc[st.session_state.data['ID'] == r['ID'], 'Date'] = test; break
        save_data(st.session_state.data); st.rerun()

elif page == "Planning & Saisie":
    st.title("🗓️ Planning & Saisie")
    # Planning Visuel 7 jours
    cols = st.columns(7)
    jours_fr = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
    for i in range(7):
        day = dt.date.today() + dt.timedelta(days=i)
        with cols[i]:
            st.markdown(f"**{jours_fr[day.weekday()]}**")
            for _, r in df[df['Date'] == day].iterrows():
                st.caption(f"{r['Matiere']} : {r['Chapitre']}")

    st.subheader("Saisie des notes (séparées par virgules)")
    # Tableau de saisie (Éditable)
    edited = st.data_editor(df, use_container_width=True)
    if st.button("Enregistrer"):
        st.session_state.data.update(edited)
        save_data(st.session_state.data); st.rerun()

elif page == "Graphiques":
    st.title("📊 Progression")
    st.bar_chart(df.groupby('Matiere')['Note'].count())