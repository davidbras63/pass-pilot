import streamlit as st
import pandas as pd
import datetime as dt
import os

st.set_page_config(layout="wide")

# --- GESTION PERSISTANCE ---
DATA_FILE = "data.csv"
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        # Force la conversion des dates pour éviter les erreurs de format
        df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
        return df
    return pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note'])

def save_data(df): df.to_csv(DATA_FILE, index=False)

if 'data' not in st.session_state: st.session_state.data = load_data()
if 'dossiers' not in st.session_state:
    st.session_state.dossiers = {"PASS": ["UE1", "UE2"]}
    st.session_state.config = {'cours_max': 5, 'cadencier': [1, 3, 7, 14, 30], 'seuils': {1: 10, 3: 12, 7: 14, 14: 15, 30: 16}}

# --- SIDEBAR ---
st.sidebar.title("⚙️ Pilot Expert")
choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.dossiers.keys()))
page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])
df = st.session_state.data[st.session_state.data['Dossier'] == choix_dos]
jours_fr = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

# --- PAGES ---
if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    st.subheader("⚠️ Alertes Rattrapage")
    # Filtre sur les notes > 0 pour éviter d'afficher tout le vide
    alertes = df[(df['Note'] > 0) & (df['Note'] < 10)]
    for idx, row in alertes.iterrows():
        if st.button(f"Planifier rattrapage : {row['Chapitre']}", key=f"p_{idx}"):
            prochaine = dt.date.today() + dt.timedelta(days=1)
            new_r = {'Dossier': choix_dos, 'Matiere': row['Matiere'], 'Chapitre': row['Chapitre'], 'J_Type': 'Rattrapage', 'Date': prochaine, 'Note': 0}
            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_r])], ignore_index=True)
            save_data(st.session_state.data); st.rerun()

elif page == "Planning & Saisie":
    st.title("🗓️ Planning & Saisie")
    with st.expander("➕ Ajouter Chapitre"):
        with st.form("Add"):
            mat = st.selectbox("Matière", st.session_state.dossiers[choix_dos])
            chap = st.text_input("Chapitre")
            d0 = st.date_input("Date J0", format="DD/MM/YYYY")
            date_exam = st.date_input("Date Examen", value=None, format="DD/MM/YYYY")
            if st.form_submit_button("Générer planning"):
                if date_exam is None: st.error("⚠️ Date d'examen obligatoire !")
                else:
                    for j in [0] + st.session_state.config['cadencier']:
                        d_sess = d0 + dt.timedelta(days=j)
                        # Exclut les dimanches (6)
                        if d_sess <= date_exam and d_sess.weekday() != 6:
                            new = {'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': f"J{j}", 'Date': d_sess, 'Note': 0}
                            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new])], ignore_index=True)
                    save_data(st.session_state.data); st.rerun()

    cols = st.columns(7)
    for i in range(7):
        day = dt.date.today() + dt.timedelta(days=i)
        with cols[i]:
            st.markdown(f"**{jours_fr[day.weekday()]} {day.strftime('%d/%m')}**")
            # Filtre de date sécurisé
            for idx, r in df[df['Date'].dt.date == day].iterrows():
                st.write(f"{r['Chapitre']} ({r['J_Type']})")
                new_d = st.date_input("Décaler au :", key=f"d_{idx}", label_visibility="collapsed", format="DD/MM/YYYY")
                if st.button("Confirmer", key=f"b_{idx}"):
                    st.session_state.data.at[idx, 'Date'] = pd.to_datetime(new_d)
                    save_data(st.session_state.data); st.rerun()

    # Saisie des notes
    edited_df = st.data_editor(st.session_state.data, use_container_width=True)
    if st.button("Enregistrer"):
        st.session_state.data = edited_df; save_data(st.session_state.data); st.rerun()