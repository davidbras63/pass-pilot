import streamlit as st
import pandas as pd
import datetime as dt

st.set_page_config(page_title="Pilot Expert", layout="wide")

# --- INITIALISATION ---
if 'init' not in st.session_state:
    st.session_state.dossiers = {"PASS": ["UE1", "UE2"]}
    st.session_state.data = pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'Date', 'Note', 'Intervalle'])
    st.session_state.config = {
        'cours_max': 5,
        'seuils': {1: 10, 3: 12, 7: 14}, # Seuil par J
        'cadencier': [1, 3, 7, 14, 30]
    }
    st.session_state.init = True

# --- SIDEBAR : GESTION TOTALE ---
st.sidebar.title("⚙️ Pilot Expert")

with st.sidebar.expander("🛠️ Réglages Complets"):
    st.session_state.config['cours_max'] = st.number_input("Max cours/jour", 1, 20, st.session_state.config['cours_max'])
    st.write("**Seuils de rattrapage par J**")
    for j in st.session_state.config['cadencier']:
        st.session_state.config['seuils'][j] = st.slider(f"Seuil J{j}", 0, 20, st.session_state.config['seuils'].get(j, 10))

# Gestion Dossiers & Matières
new_dos = st.sidebar.text_input("Ajouter Dossier")
if st.sidebar.button("Créer Dossier") and new_dos:
    st.session_state.dossiers[new_dos] = []
    st.rerun()

choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.dossiers.keys()))

new_mat = st.sidebar.text_input("Ajouter Matière")
if st.sidebar.button("Ajouter Matière") and new_mat:
    st.session_state.dossiers[choix_dos].append(new_mat)
    st.rerun()

page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Notes", "Suivi & Graphiques"])

# --- LOGIQUE ---
df = st.session_state.data[st.session_state.data['Dossier'] == choix_dos]

# --- PAGES ---
if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    # Métriques
    c1, c2, c3 = st.columns(3)
    c1.metric("Matières", len(st.session_state.dossiers[choix_dos]))
    c2.metric("Moyenne", f"{df[df['Note']>0]['Note'].mean():.1f}/20")
    
    st.subheader("⚠️ Alertes Rattrapage")
    # Affiche tout ce qui est sous le seuil défini dans les réglages
    st.dataframe(df[df['Note'] < 10], use_container_width=True)
    
    st.subheader("Matières actives")
    st.write(st.session_state.dossiers[choix_dos])

elif page == "Planning & Notes":
    st.title("🗓️ Planning Hebdo & Saisie")
    
    # Formulaire d'ajout
    with st.form("Add_Chapitre"):
        mat = st.selectbox("Matière", st.session_state.dossiers[choix_dos])
        nom = st.text_input("Nom Chapitre")
        d0 = st.date_input("Date")
        if st.form_submit_button("Ajouter au Planning"):
            new_row = pd.DataFrame([{'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': nom, 'Date': d0, 'Note': 0, 'Intervalle': 0}])
            st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
            st.rerun()
            
    # Planning Visuel
    st.subheader(f"Planning - Semaine {dt.date.today().strftime('%V')}")
    cols = st.columns(7)
    today = dt.date.today()
    for i in range(7):
        day = today + dt.timedelta(days=i)
        with cols[i]:
            st.markdown(f"**{day.strftime('%A %d')}**")
            for _, r in df[df['Date'] == day].iterrows():
                st.info(f"{r['Matiere']}\n{r['Chapitre']}")

    st.subheader("✏️ Saisie des Notes")
    if not df.empty:
        id_l = st.number_input("ID Ligne", 0, len(df)-1)
        note = st.slider("Note", 0, 20)
        if st.button("Valider Note"):
            st.session_state.data.loc[df.index[id_l], 'Note'] = note
            st.rerun()
        st.dataframe(df, use_container_width=True)

elif page == "Suivi & Graphiques":
    st.title("📊 Évolution")
    for m in st.session_state.dossiers[choix_dos]:
        st.subheader(m)
        st.line_chart(df[df['Matiere'] == m].set_index('Date')['Note'])