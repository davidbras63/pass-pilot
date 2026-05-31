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
with st.sidebar.expander("🛠️ Réglages complets"):
    st.session_state.config['cours_max'] = st.number_input("Max cours/jour", 1, 20, st.session_state.config['cours_max'])
    cad_str = st.text_input("Cadencier", ",".join(map(str, st.session_state.config['cadencier'])))
    st.session_state.config['cadencier'] = [int(x.strip()) for x in cad_str.split(",")]
    st.write("**Seuils de rattrapage**")
    for j in st.session_state.config['cadencier']:
        st.session_state.config['seuils'][j] = st.slider(f"Seuil J{j}", 0, 20, st.session_state.config['seuils'].get(j, 10))

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
    # ... (le reste du dashboard est conservé identique)
    # [Note : Le code du Dashboard reste celui validé précédemment]
    for m in st.session_state.dossiers[choix_dos]:
        col1, col2 = st.columns([4, 1])
        col1.info(f"{m} : {len(df[df['Matiere'] == m])} sessions")
        if col2.button("🗑️", key=f"del_{m}"):
            st.session_state.dossiers[choix_dos].remove(m)
            st.rerun()

elif page == "Planning & Saisie":
    st.title("🗓️ Planning & Saisie")
    with st.expander("➕ Ajouter Chapitre"):
        with st.form("Add"):
            mat = st.selectbox("Matière", st.session_state.dossiers[choix_dos])
            chap = st.text_input("Nom du Chapitre")
            d0 = st.date_input("Date J0")
            date_examen = st.date_input("Date de l'examen")
            if st.form_submit_button("Générer tout le planning"):
                for j in [0] + st.session_state.config['cadencier']:
                    date_session = d0 + dt.timedelta(days=j)
                    if date_session <= date_examen:
                        new_row = {'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 
                                   'J_Type': f"J{j}", 'Date': date_session, 'Note': 0}
                        st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=True)
                save_data(st.session_state.data)
                st.rerun()

    cols = st.columns(7)
    today = dt.date.today()
    for i in range(7):
        day = today + dt.timedelta(days=i)
        with cols[i]:
            st.markdown(f"**{day.strftime('%A %d')}**")
            # Affichage des cours du jour avec option de report
            for idx, r in df[df['Date'].astype(str) == str(day)].iterrows():
                st.write(f"**{r['Chapitre']}** ({r['J_Type']})")
                new_date = st.date_input("Décaler au :", key=f"move_{idx}", label_visibility="collapsed")
                if st.button("Confirmer report", key=f"btn_{idx}"):
                    st.session_state.data.at[idx, 'Date'] = new_date
                    save_data(st.session_state.data)
                    st.rerun()

    st.markdown("---")
    st.subheader("✏️ Saisie des Notes")
    df_with_id = st.session_state.data.copy()
    df_with_id.insert(0, 'ID', df_with_id.index)
    edited_df = st.data_editor(df_with_id, use_container_width=True)
    if st.button("Enregistrer les notes"):
        st.session_state.data = edited_df.drop(columns=['ID'])
        save_data(st.session_state.data)
        st.rerun()

elif page == "Graphiques":
    st.title("📊 Progression par Chapitre")
    if not df.empty:
        stats = df[df['Note'] > 0].groupby('Chapitre')['Note'].mean()
        st.bar_chart(stats)