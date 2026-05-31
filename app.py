import streamlit as st
import pandas as pd
import datetime as dt
import os

st.set_page_config(layout="wide")

# --- GESTION PERSISTANCE ---
DATA_FILE = "data.csv"
def load_data():
    if os.path.exists(DATA_FILE): return pd.read_csv(DATA_FILE, parse_dates=['Date'])
    return pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note'])

def save_data(df): df.to_csv(DATA_FILE, index=False)

if 'data' not in st.session_state: st.session_state.data = load_data()
if 'dossiers' not in st.session_state:
    st.session_state.dossiers = {"PASS": ["UE1", "UE2"]}
    st.session_state.config = {'cadencier': [1, 3, 7, 14, 30]}

# --- SIDEBAR ---
st.sidebar.title("⚙️ Pilot Expert")
choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.dossiers.keys()))
new_mat = st.sidebar.text_input("Nouvelle Matière")
if st.sidebar.button("Ajouter") and new_mat: st.session_state.dossiers[choix_dos].append(new_mat)

page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie"])
df = st.session_state.data[st.session_state.data['Dossier'] == choix_dos]

# --- PAGES ---
if page == "Dashboard":
    st.title("🎯 Dashboard")
    alertes = df[(df['Note'] > 0) & (df['Note'] < 10)]
    for idx, row in alertes.iterrows():
        st.warning(f"Rattrapage : {row['Chapitre']} ({row['Matiere']})")
        if st.button(f"Planifier {row['Chapitre']}", key=f"plan_{idx}"):
            # Recherche intelligente : 1 à 14 jours, lundi au samedi (pas dimanche)
            date_test = dt.date.today() + dt.timedelta(days=1)
            found = False
            for _ in range(30):
                # Si jour < dimanche (6) et date libre
                if date_test.weekday() < 6 and st.session_state.data[st.session_state.data['Date'].astype(str) == str(date_test)].empty:
                    new_r = {'Dossier': choix_dos, 'Matiere': row['Matiere'], 'Chapitre': row['Chapitre'], 
                             'J_Type': 'Rattrapage', 'Date': date_test, 'Note': 0}
                    st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_r])], ignore_index=True)
                    found = True; break
                date_test += dt.timedelta(days=1)
            save_data(st.session_state.data); st.rerun()

elif page == "Planning & Saisie":
    st.title("🗓️ Planning")
    with st.expander("➕ Ajouter Chapitre"):
        with st.form("Add"):
            mat = st.selectbox("Matière", st.session_state.dossiers[choix_dos])
            chap = st.text_input("Chapitre")
            d0 = st.date_input("Date J0 (JJ/MM/AAAA)", format="DD/MM/YYYY")
            date_exam = st.date_input("Date Examen (JJ/MM/AAAA)", value=None, format="DD/MM/YYYY")
            if st.form_submit_button("Valider"):
                if not date_exam: st.error("Saisir la date de l'examen !")
                else:
                    for j in [0] + st.session_state.config['cadencier']:
                        d_sess = d0 + dt.timedelta(days=j)
                        # Génération auto : ignore les dimanches
                        if d_sess <= date_exam and d_sess.weekday() != 6:
                            new = {'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 
                                   'J_Type': f"J{j}", 'Date': d_sess, 'Note': 0}
                            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new])], ignore_index=True)
                    save_data(st.session_state.data); st.rerun()

    cols = st.columns(7)
    jours_fr = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    for i in range(7):
        day = dt.date.today() + dt.timedelta(days=i)
        with cols[i]:
            st.write(f"**{jours_fr[day.weekday()]} {day.strftime('%d/%m')}**")
            for idx, r in df[df['Date'].astype(str) == str(day)].iterrows():
                st.info(f"{r['Matiere']} - {r['Chapitre']} ({r['J_Type']})")
                new_d = st.date_input("Décaler au :", key=f"d_{idx}", label_visibility="collapsed", format="DD/MM/YYYY")
                if st.button("Confirmer", key=f"b_{idx}"):
                    st.session_state.data.at[idx, 'Date'] = new_d
                    save_data(st.session_state.data); st.rerun()