import streamlit as st
import pandas as pd
import datetime as dt

st.set_page_config(layout="wide")

# --- INITIALISATION ROBUSTE (Remise à zéro propre) ---
if 'init' not in st.session_state:
    st.session_state.dossiers = {"PASS": ["UE1", "UE2"]}
    st.session_state.data = pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'Date', 'Note'])
    st.session_state.cadencier = [1, 3, 7, 14, 30]
    st.session_state.seuil = 10
    st.session_state.init = True

# --- SIDEBAR (PARAMÈTRES) ---
st.sidebar.title("⚙️ Pilot Expert")
with st.sidebar.expander("🛠️ Réglages"):
    st.session_state.seuil = st.number_input("Seuil rattrapage", 0, 20, st.session_state.seuil)
    cad_str = st.text_input("Cadencier (jours, ex: 1,3,7)", ",".join(map(str, st.session_state.cadencier)))
    st.session_state.cadencier = [int(x.strip()) for x in cad_str.split(",")]

choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.dossiers.keys()))
page = st.sidebar.radio("Navigation", ["Dashboard", "Planning Hebdo", "Saisie & Rattrapage"])

# --- LOGIQUE ---
df = st.session_state.data[st.session_state.data['Dossier'] == choix_dos]

if page == "Dashboard":
    st.title("🎯 Dashboard")
    c1, c2, c3 = st.columns(3)
    c1.metric("Matières", len(st.session_state.dossiers[choix_dos]))
    c2.metric("Moyenne", f"{df[df['Note']>0]['Note'].mean():.1f}/20" if not df[df['Note']>0].empty else "0/20")
    
    st.subheader("Matières")
    st.write(st.session_state.dossiers[choix_dos])

elif page == "Planning Hebdo":
    st.title(f"🗓️ Planning Hebdo")
    
    # Ajout de cours
    with st.expander("➕ Ajouter un cours"):
        with st.form("add_cours"):
            mat = st.selectbox("Matière", st.session_state.dossiers[choix_dos])
            nom = st.text_input("Nom chapitre")
            d0 = st.date_input("Date")
            if st.form_submit_button("Ajouter"):
                new_row = pd.DataFrame([{'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': nom, 'Date': d0, 'Note': 0}])
                st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
                st.rerun()

    # Vue calendrier 7 jours
    cols = st.columns(7)
    today = dt.date.today()
    for i in range(7):
        jour = today + dt.timedelta(days=i)
        with cols[i]:
            st.markdown(f"**{jour.strftime('%a %d')}**")
            for _, row in df[df['Date'] == jour].iterrows():
                st.info(f"{row['Matiere']}: {row['Chapitre']}")

elif page == "Saisie & Rattrapage":
    st.title("✏️ Saisie & Évolution")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        id_l = st.number_input("ID ligne à noter", 0, len(df)-1)
        note = st.slider("Note", 0, 20)
        
        if st.button("Valider"):
            st.session_state.data.loc[df.index[id_l], 'Note'] = note
            # Rattrapage
            if note < st.session_state.seuil:
                old_date = st.session_state.data.loc[df.index[id_l], 'Date']
                st.session_state.data.loc[df.index[id_l], 'Date'] = old_date + dt.timedelta(days=st.session_state.cadencier[0])
                st.warning("Note < seuil : reporté au prochain créneau.")
            st.rerun()
            
    st.line_chart(df.set_index('Date')['Note'])