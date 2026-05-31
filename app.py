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

# --- INITIALISATION ---
if 'data' not in st.session_state: st.session_state.data = load_data()
if 'dossiers' not in st.session_state:
    st.session_state.dossiers = {"PASS": ["UE1", "UE2"]}
    st.session_state.config = {'cours_max': 5, 'cadencier': [1, 3, 7, 14, 30], 'seuils': {1: 10, 3: 12, 7: 14, 14: 15, 30: 16}}

# --- SIDEBAR ---
st.sidebar.title("⚙️ Pilot Expert")
choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.dossiers.keys()))
new_mat = st.sidebar.text_input("Ajouter Matière")
if st.sidebar.button("Ajouter Matière") and new_mat: st.session_state.dossiers[choix_dos].append(new_mat)
page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])

# --- LOGIQUE ---
df = st.session_state.data[st.session_state.data['Dossier'] == choix_dos]
jours_fr = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

# --- PAGES ---
if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    # Liste des rattrapages
    alertes = df[(df['Note'] > 0) & (df['Note'] < 10)]
    for idx, row in alertes.iterrows():
        if st.button(f"Planifier rattrapage : {row['Chapitre']} ({row['Matiere']})", key=f"plan_{idx}"):
            # Recherche créneau : lundi(0) à samedi(5) d'abord
            found = False
            for delta in range(1, 15):
                test_date = dt.date.today() + dt.timedelta(days=delta)
                if test_date.weekday() < 6 and st.session_state.data[st.session_state.data['Date'].astype(str) == str(test_date)].empty:
                    st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([{'Dossier': choix_dos, 'Matiere': row['Matiere'], 'Chapitre': row['Chapitre'], 'J_Type': 'Rattrapage', 'Date': test_date, 'Note': 0}])], ignore_index=True)
                    found = True; break
            if not found: # Si rien en semaine, autorise dimanche
                new_date = dt.date.today() + dt.timedelta(days=1)
                st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([{'Dossier': choix_dos, 'Matiere': row['Matiere'], 'Chapitre': row['Chapitre'], 'J_Type': 'Rattrapage', 'Date': new_date, 'Note': 0}])], ignore_index=True)
            save_data(st.session_state.data); st.rerun()

elif page == "Planning & Saisie":
    st.title("🗓️ Planning & Saisie")
    with st.expander("➕ Ajouter Chapitre"):
        with st.form("Add"):
            mat = st.selectbox("Matière", st.session_state.dossiers[choix_dos])
            chap = st.text_input("Nom du Chapitre")
            d0 = st.date_input("Date J0", format="DD/MM/YYYY")
            date_examen = st.date_input("Date de l'examen", value=None, format="DD/MM/YYYY")
            if st.form_submit_button("Générer tout le planning"):
                if date_examen is None: st.error("⚠️ Vous devez choisir une date d'examen.")
                else:
                    for j in [0] + st.session_state.config['cadencier']:
                        d_sess = d0 + dt.timedelta(days=j)
                        # Dimanche (6) exclu de la génération automatique
                        if d_sess <= date_examen and d_sess.weekday() != 6:
                            new_row = {'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': f"J{j}", 'Date': d_sess, 'Note': 0}
                            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=True)
                    save_data(st.session_state.data); st.rerun()

    cols = st.columns(7)
    today = dt.date.today()
    for i in range(7):
        day = today + dt.timedelta(days=i)
        with cols[i]:
            st.markdown(f"**{jours_fr[day.weekday()]} {day.strftime('%d/%m')}**")
            for idx, r in df[df['Date'].astype(str) == str(day)].iterrows():
                st.write(f"**{r['Chapitre']}** ({r['J_Type']})")
                new_d = st.date_input("Reporter :", key=f"d_{idx}", label_visibility="collapsed", format="DD/MM/YYYY")
                if st.button("Valider", key=f"b_{idx}"):
                    st.session_state.data.at[idx, 'Date'] = new_d
                    save_data(st.session_state.data); st.rerun()

    st.subheader("✏️ Saisie Notes")
    df_with_id = st.session_state.data.copy()
    df_with_id.insert(0, 'ID', df_with_id.index)
    edited_df = st.data_editor(df_with_id, use_container_width=True)
    if st.button("Enregistrer"):
        st.session_state.data = edited_df.drop(columns=['ID']); save_data(st.session_state.data); st.rerun()

elif page == "Graphiques":
    st.title("📊 Progression")