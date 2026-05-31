import streamlit as st
import pandas as pd
import datetime as dt
import os

st.set_page_config(layout="wide")

DATA_FILE = "data.csv"

def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        # Nettoyage automatique des noms de colonnes pour éviter les KeyError
        df.columns = df.columns.str.strip() 
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
        return df
    return pd.DataFrame(columns=['ID', 'Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note'])

def save_data(df): df.to_csv(DATA_FILE, index=False)

if 'data' not in st.session_state: st.session_state.data = load_data()
if 'dossiers' not in st.session_state:
    st.session_state.dossiers = {"PASS": ["UE1", "UE2"]}
    st.session_state.config = {'cours_max': 5, 'cadencier': [1, 3, 7, 14, 30], 'seuils': {1: 10, 3: 12, 7: 14, 14: 15, 30: 16}}

# --- SIDEBAR (Réglages) ---
st.sidebar.title("⚙️ Pilot Expert")
with st.sidebar.expander("🛠️ Réglages"):
    st.session_state.config['cours_max'] = st.number_input("Max cours/jour", 1, 20, st.session_state.config['cours_max'])
    cad_str = st.text_input("Cadencier", ",".join(map(str, st.session_state.config['cadencier'])))
    st.session_state.config['cadencier'] = [int(x.strip()) for x in cad_str.split(",")]
    for j in st.session_state.config['cadencier']:
        st.session_state.config['seuils'][j] = st.slider(f"Seuil J{j}", 0, 20, st.session_state.config['seuils'].get(j, 10))

choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.dossiers.keys()))
page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])
df = st.session_state.data[st.session_state.data['Dossier'] == choix_dos].copy()

# --- PAGES ---
if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    if st.button("🚀 Placer rattrapages dans les trous"):
        for _, r in df.iterrows():
            notes = str(r['Note']).split(',')
            if notes and notes[0] != '0' and float(notes[-1]) < st.session_state.config['seuils'].get(int(str(r['J_Type']).replace('J','')), 10):
                for i in range(1, 8):
                    test_date = dt.date.today() + dt.timedelta(days=i)
                    if test_date.weekday() < 6 and len(df[df['Date'] == test_date]) < st.session_state.config['cours_max']:
                        st.session_state.data.loc[st.session_state.data['ID'] == r['ID'], 'Date'] = test_date; break
        save_data(st.session_state.data); st.rerun()
    st.table(df)

elif page == "Planning & Saisie":
    st.title("🗓️ Planning & Saisie")
    with st.expander("➕ Ajouter Chapitre"):
        with st.form("Add"):
            mat = st.selectbox("Matière", st.session_state.dossiers.get(choix_dos, []))
            chap = st.text_input("Nom du Chapitre")
            d0 = st.date_input("Date J0", format="DD/MM/YYYY")
            date_exam = st.date_input("Date examen", value=None, format="DD/MM/YYYY")
            if st.form_submit_button("Générer"):
                for j in [0] + st.session_state.config['cadencier']:
                    d_sess = d0 + dt.timedelta(days=j)
                    if d_sess.weekday() != 6 and (not date_exam or d_sess <= date_exam):
                        new_row = {'ID': len(st.session_state.data), 'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': f"J{j}", 'Date': d_sess, 'Note': '0'}
                        st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=True)
                save_data(st.session_state.data); st.rerun()

    # Le tableau qui posait problème : affichage dynamique sans forcer les noms de colonnes
    edited_planning = st.data_editor(df, use_container_width=True, hide_index=True)
    if st.button("Enregistrer les modifs"):
        st.session_state.data.update(edited_planning)
        save_data(st.session_state.data); st.rerun()

elif page == "Graphiques":
    st.title("📊 Progression")