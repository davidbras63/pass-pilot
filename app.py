import streamlit as st
import pandas as pd
import datetime as dt

st.set_page_config(layout="wide")

# --- INITIALISATION ---
if 'dossiers' not in st.session_state:
    st.session_state.dossiers = {"PASS": ["UE1", "UE2"]}
    st.session_state.data = pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'Date', 'Note'])
    st.session_state.cadencier = [1, 3, 7, 14, 30]
    st.session_state.seuils = {j: 10 for j in st.session_state.cadencier}

# --- SIDEBAR : RÉGLAGES ---
st.sidebar.title("⚙️ Pilot Expert")
with st.sidebar.expander("🛠️ Réglages (Cadencier & Seuils)"):
    cad_str = st.text_input("Jours du cadencier (ex: 1,3,7,14,30,60,90)", ",".join(map(str, st.session_state.cadencier)))
    st.session_state.cadencier = [int(x.strip()) for x in cad_str.split(",")]
    
    st.write("**Seuils de rattrapage par J**")
    for j in st.session_state.cadencier:
        if j not in st.session_state.seuils: st.session_state.seuils[j] = 10
        st.session_state.seuils[j] = st.slider(f"Seuil J{j}", 0, 20, st.session_state.seuils[j])

choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.dossiers.keys()))
new_mat = st.sidebar.text_input("Nouvelle matière")
if st.sidebar.button("Ajouter") and new_mat:
    st.session_state.dossiers[choix_dos].append(new_mat)
    st.rerun()

page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])

# --- LOGIQUE ---
df = st.session_state.data[st.session_state.data['Dossier'] == choix_dos]

# --- PAGES ---
if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    st.subheader("📋 Matières")
    for m in st.session_state.dossiers[choix_dos]: st.info(m) # Liste verticale
    st.subheader("⚠️ Alertes Rattrapage")
    st.dataframe(df[df['Note'] < 10], use_container_width=True)

elif page == "Planning & Saisie":
    st.title("🗓️ Planning Hebdo")
    with st.form("Add"):
        mat = st.selectbox("Matière", st.session_state.dossiers[choix_dos])
        nom = st.text_input("Chapitre")
        d0 = st.date_input("Date")
        if st.form_submit_button("Ajouter"):
            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([{'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': nom, 'Date': d0, 'Note': 0}])])
            st.rerun()
    
    # Planning Visuel
    cols = st.columns(7)
    for i, day in enumerate([(dt.date.today() + dt.timedelta(days=i)) for i in range(7)]):
        with cols[i]:
            st.markdown(f"**{day.strftime('%A %d')}**")
            for _, r in df[df['Date'] == day].iterrows():
                st.write(f"• {r['Matiere']}: {r['Chapitre']}")

    st.subheader("✏️ Saisie des Notes")
    if not df.empty:
        id_l = st.number_input("ID ligne (voir tableau)", 0, len(df)-1)
        note = st.slider("Note", 0, 20)
        if st.button("Valider"):
            st.session_state.data.loc[df.index[id_l], 'Note'] = note
            st.rerun()
        st.dataframe(df, use_container_width=True)

elif page == "Graphiques":
    st.title("📊 Évolution")
    for m in st.session_state.dossiers[choix_dos]:
        st.subheader(f"Matière : {m}")
        m_df = df[df['Matiere'] == m]
        if not m_df.empty: st.line_chart(m_df.set_index('Date')['Note'])