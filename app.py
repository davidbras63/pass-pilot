import streamlit as st
import pandas as pd
import datetime as dt
import os

st.set_page_config(layout="wide")

# --- PERSISTANCE ---
DATA_FILE = "data.csv"
def load_data():
    if os.path.exists(DATA_FILE): 
        df = pd.read_csv(DATA_FILE, parse_dates=['Date'])
        if 'ID' not in df.columns: df.insert(0, 'ID', df.index)
        return df
    return pd.DataFrame(columns=['ID', 'Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note'])

def save_data(df): df.to_csv(DATA_FILE, index=False)

if 'data' not in st.session_state: st.session_state.data = load_data()
if 'dossiers' not in st.session_state:
    st.session_state.dossiers = {"PASS": ["UE1", "UE2"]}
    st.session_state.config = {'cours_max': 5, 'cadencier': [1, 3, 7, 14, 30], 'seuils': {1: 10, 3: 12, 7: 14, 14: 15, 30: 16}}

# --- SIDEBAR ---
st.sidebar.title("⚙️ Pilot Expert")
with st.sidebar.expander("🛠️ Réglages complets"):
    st.session_state.config['cours_max'] = st.number_input("Max cours/jour", 1, 20, st.session_state.config['cours_max'])
    cad_str = st.text_input("Cadencier", ",".join(map(str, st.session_state.config['cadencier'])))
    st.session_state.config['cadencier'] = [int(x.strip()) for x in cad_str.split(",")]
    for j in st.session_state.config['cadencier']:
        st.session_state.config['seuils'][j] = st.slider(f"Seuil J{j}", 0, 20, st.session_state.config['seuils'].get(j, 10))

new_dos = st.sidebar.text_input("Créer Dossier")
if st.sidebar.button("Ajouter Dossier") and new_dos: 
    st.session_state.dossiers[new_dos] = []
    st.rerun()

choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.dossiers.keys()))
new_mat = st.sidebar.text_input("Ajouter Matière")
if st.sidebar.button("Ajouter Matière") and new_mat: st.session_state.dossiers[choix_dos].append(new_mat)

page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])
df = st.session_state.data[st.session_state.data['Dossier'] == choix_dos]
jours_fr = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

# --- PAGES ---
if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    st.subheader("Matières suivies")
    for m in st.session_state.dossiers[choix_dos]:
        col1, col2 = st.columns([4, 1])
        col1.info(f"{m} : {len(df[df['Matiere'] == m])} sessions")
        if col2.button("🗑️", key=f"del_{m}"):
            st.session_state.dossiers[choix_dos].remove(m)
            st.rerun()
        
    st.subheader("⚠️ Alertes Rattrapage")
    for idx, row in df.iterrows():
        if row['Note'] > 0:
            j_num = int(row['J_Type'].replace('J', '')) if 'J' in str(row['J_Type']) else 0
            if row['Note'] < st.session_state.config['seuils'].get(j_num, 10):
                if st.button(f"Planifier rattrapage : {row['Chapitre']} (ID: {row['ID']})", key=f"plan_{idx}"):
                    new_id = st.session_state.data['ID'].max() + 1 if not st.session_state.data.empty else 0
                    new_r = {'ID': new_id, 'Dossier': choix_dos, 'Matiere': row['Matiere'], 'Chapitre': row['Chapitre'], 'J_Type': 'Rattrapage', 'Date': dt.date.today() + dt.timedelta(days=1), 'Note': 0}
                    st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_r])], ignore_index=True)
                    save_data(st.session_state.data); st.rerun()

elif page == "Planning & Saisie":
    st.title("🗓️ Planning & Saisie")
    with st.expander("➕ Ajouter Chapitre"):
        with st.form("Add"):
            mat = st.selectbox("Matière", st.session_state.dossiers[choix_dos])
            chap = st.text_input("Nom du Chapitre")
            d0 = st.date_input("Date J0", format="DD/MM/YYYY")
            date_exam = st.date_input("Date de l'examen", value=None, format="DD/MM/YYYY")
            if st.form_submit_button("Générer planning"):
                if date_exam is None: st.error("⚠️ La date de l'examen est obligatoire !")
                else:
                    for j in [0] + st.session_state.config['cadencier']:
                        d_sess = d0 + dt.timedelta(days=j)
                        if d_sess <= date_exam and d_sess.weekday() != 6:
                            new_id = st.session_state.data['ID'].max() + 1 if not st.session_state.data.empty else 0
                            new_row = {'ID': new_id, 'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': f"J{j}", 'Date': d_sess, 'Note': 0}
                            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=True)
                    save_data(st.session_state.data); st.rerun()

    cols = st.columns(7)
    for i in range(7):
        day = dt.date.today() + dt.timedelta(days=i)
        with cols[i]:
            st.write(f"**{jours_fr[day.weekday()]} {day.strftime('%d/%m')}**")
            for idx, r in df[df['Date'].astype(str) == str(day)].iterrows():
                st.write(f"{r['Chapitre']} ({r['J_Type']} - ID: {r['ID']})")
                new_date = st.date_input("Décaler au :", key=f"d_{idx}", label_visibility="collapsed", format="DD/MM/YYYY")
                if st.button("Confirmer report", key=f"b_{idx}"):
                    st.session_state.data.at[idx, 'Date'] = new_date
                    save_data(st.session_state.data); st.rerun()

    st.markdown("---")
    st.subheader("✏️ Saisie des Notes par ID")
    edited_df = st.data_editor(st.session_state.data, use_container_width=True, hide_index=True)
    if st.button("Enregistrer les notes"):
        st.session_state.data = edited_df
        save_data(st.session_state.data)
        st.rerun()

elif page == "Graphiques":
    st.title("📊 Progression")
    if not df.empty: st.bar_chart(df[df['Note'] > 0].groupby('Chapitre')['Note'].mean())