import streamlit as st
import pandas as pd
import datetime as dt

st.set_page_config(layout="wide")

# --- INITIALISATION ---
if 'dossiers' not in st.session_state:
    st.session_state.dossiers = {"PASS": ["UE1", "UE2"]}
    st.session_state.data = pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'Date', 'Note', 'Intervalle'])
    st.session_state.cadencier = [1, 3, 7, 14, 30] # Modifiable
    st.session_state.seuil = 10

# --- SIDEBAR ---
st.sidebar.title("Pilot Expert")
with st.sidebar.expander("🛠️ Paramètres"):
    st.session_state.seuil = st.number_input("Seuil rattrapage", 0, 20, st.session_state.seuil)
    cad_str = st.text_input("Cadencier (Jours)", ",".join(map(str, st.session_state.cadencier)))
    st.session_state.cadencier = [int(x.strip()) for x in cad_str.split(",")]

choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.dossiers.keys()))
page = st.sidebar.radio("Navigation", ["Dashboard", "Planning Hebdo", "Suivi & Rattrapage"])

# --- LOGIQUE ---
df = st.session_state.data[st.session_state.data['Dossier'] == choix_dos]

if page == "Dashboard":
    st.title("🎯 Pilotage")
    st.metric("Moyenne Globale", f"{df[df['Note']>0]['Note'].mean():.1f}/20")
    st.write("Matières :", st.session_state.dossiers[choix_dos])

elif page == "Planning Hebdo":
    st.title(f"🗓️ Semaine du {dt.date.today().strftime('%W')}")
    
    with st.expander("➕ Ajouter un chapitre"):
        with st.form("add"):
            mat = st.selectbox("Matière", st.session_state.dossiers[choix_dos])
            nom = st.text_input("Nom")
            d0 = st.date_input("Date")
            if st.form_submit_button("Ajouter"):
                new_row = pd.DataFrame([{'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': nom, 'Date': d0, 'Note': 0, 'Intervalle': 0}])
                st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
                st.rerun()

    # Affichage Colonnes Lundi-Dimanche
    cols = st.columns(7)
    today = dt.date.today()
    for i in range(7):
        curr_day = today + dt.timedelta(days=i)
        with cols[i]:
            st.markdown(f"**{curr_day.strftime('%a %d')}**")
            for _, row in df[df['Date'] == curr_day].iterrows():
                st.info(f"{row['Matiere']}: {row['Chapitre']}")

elif page == "Suivi & Rattrapage":
    st.title("✏️ Saisie & Rattrapage")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        id_row = st.number_input("ID ligne", 0, len(df)-1)
        note = st.slider("Note", 0, 20)
        
        if st.button("Valider et traiter"):
            # Update note
            st.session_state.data.loc[df.index[id_row], 'Note'] = note
            
            # Logique Rattrapage : si < seuil, on replanifie
            if note < st.session_state.seuil:
                old_date = st.session_state.data.loc[df.index[id_row], 'Date']
                next_j = st.session_state.cadencier[0] # Prochain intervalle
                new_date = old_date + dt.timedelta(days=next_j)
                st.warning(f"Note insuffisante. Reporté à {new_date}")
                st.session_state.data.loc[df.index[id_row], 'Date'] = new_date
            st.rerun()
            
    st.line_chart(df.set_index('Date')['Note'])
