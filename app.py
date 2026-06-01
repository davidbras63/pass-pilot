import streamlit as st
import pandas as pd
import datetime as dt
import os, json

st.set_page_config(layout="wide")
DATA_FILE, CONFIG_FILE = "data.csv", "config.json"

def save_data(df): df.drop_duplicates().to_csv(DATA_FILE, index=False)
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE).drop_duplicates()
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        return df
    return pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note', 'Statut', 'Date_Examen'])

if 'data' not in st.session_state: st.session_state.data = load_data()
if 'config' not in st.session_state: 
    with open(CONFIG_FILE, "r") as f: st.session_state.config = json.load(f)

# --- NAVIGATION & DASHBOARD ---
page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])
choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.config['dossiers'].keys()))

if page == "Dashboard":
    st.title("🎯 Dashboard")
    df = st.session_state.data[st.session_state.data['Dossier'] == choix_dos]
    rattrapages = df[(df['Note'] > 0) & (df['Note'] < 12)]
    st.table(rattrapages[['Matiere', 'Chapitre', 'J_Type', 'Note']])
    if st.button("🔄 Réintégrer Rattrapages"):
        for _, r in rattrapages.iterrows():
            new_r = r.copy(); new_r['Date'] = dt.date.today(); new_r['J_Type'] = 'RAT'; new_r['Note'] = 0
            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_r])])
        st.session_state.data = st.session_state.data.drop(rattrapages.index)
        save_data(st.session_state.data); st.rerun()

elif page == "Planning & Saisie":
    # ✍️ AJOUT
    with st.expander("✍️ Ajouter Chapitre", expanded=True):
        with st.form("Add"):
            mat = st.selectbox("Matière", st.session_state.config['dossiers'][choix_dos])
            chap = st.text_input("Titre Chapitre")
            d0, dex = st.date_input("Date J0"), st.date_input("Date Examen")
            if st.form_submit_button("Générer"):
                for j in [0] + st.session_state.config['cadencier']:
                    st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([{'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': f'J{j}', 'Date': d0 + dt.timedelta(days=j), 'Note': 0, 'Statut': 'À faire', 'Date_Examen': dex}])])
                save_data(st.session_state.data); st.rerun()

    # 🗓️ PLANNING VISUEL
    st.subheader("Planning")
    cols = st.columns(7)
    for i, day in enumerate([dt.date.today() + dt.timedelta(days=x) for x in range(7)]):
        with cols[i]:
            st.markdown(f"**{day.strftime('%d/%m')}**")
            for idx, r in st.session_state.data[(st.session_state.data['Date'] == day) & (st.session_state.data['Dossier'] == choix_dos)].iterrows():
                with st.expander(f"{r['Matiere']} ({r['J_Type']})"):
                    st.write(f"📖 **{r['Chapitre']}**")
                    if st.button("✅ Fait", key=f"f_{idx}"): st.session_state.data.at[idx, 'Statut'] = 'Fait'; save_data(st.session_state.data); st.rerun()

    # 📝 SAISIE NOTES
    st.subheader("📝 Saisie Notes")
    df_today = st.session_state.data[(st.session_state.data['Date'] == dt.date.today()) & (st.session_state.data['Dossier'] == choix_dos)]
    edited = st.data_editor(df_today[['Matiere', 'Chapitre', 'J_Type', 'Note']])
    if st.button("Enregistrer Notes"): st.session_state.data.update(edited); save_data(st.session_state.data); st.rerun()

elif page == "Graphiques":
    for mat in st.session_state.config['dossiers'][choix_dos]:
        st.subheader(f"📊 {mat}")
        st.line_chart(st.session_state.data[(st.session_state.data['Matiere'] == mat) & (st.session_state.data['Note'] > 0)].set_index('Date')['Note'])