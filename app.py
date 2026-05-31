import streamlit as st
import pandas as pd
import datetime as dt

st.set_page_config(layout="wide")

# --- INITIALISATION ---
if 'dossiers' not in st.session_state:
    st.session_state.dossiers = {"PASS": ["UE1", "UE2"]}
    st.session_state.data = pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note'])
    st.session_state.config = {'cours_max': 5, 'cadencier': [1, 3, 7, 14, 30]}

# --- SIDEBAR (Design conservé) ---
st.sidebar.title("⚙️ Pilot Expert")
with st.sidebar.expander("🛠️ Réglages"):
    st.session_state.config['cours_max'] = st.number_input("Max cours/jour", 1, 20, st.session_state.config['cours_max'])
    cad_str = st.text_input("Cadencier", ",".join(map(str, st.session_state.config['cadencier'])))
    st.session_state.config['cadencier'] = [int(x.strip()) for x in cad_str.split(",")]

choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.dossiers.keys()))
new_mat = st.sidebar.text_input("Ajouter Matière")
if st.sidebar.button("Ajouter") and new_mat: st.session_state.dossiers[choix_dos].append(new_mat)

page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])

# --- LOGIQUE ---
df = st.session_state.data[st.session_state.data['Dossier'] == choix_dos]

# --- PAGES ---
if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    for m in st.session_state.dossiers[choix_dos]:
        nb = len(df[df['Matiere'] == m])
        st.write(f"**{m}** : {nb} sessions de révision")
    st.subheader("⚠️ Alertes Rattrapage")
    st.dataframe(df[(df['Note'] > 0) & (df['Note'] < 10)], use_container_width=True)

elif page == "Planning & Saisie":
    st.title("🗓️ Planning Automatisé")
    
    with st.expander("➕ Ajouter un nouveau Chapitre (Génère le J0 + J-échéances)"):
        with st.form("Add"):
            mat = st.selectbox("Matière", st.session_state.dossiers[choix_dos])
            chap = st.text_input("Nom du Chapitre")
            d0 = st.date_input("Date J0")
            if st.form_submit_button("Générer tout le planning"):
                # Génération auto
                for j in [0] + st.session_state.config['cadencier']:
                    new_row = {'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 
                               'J_Type': f"J{j}", 'Date': d0 + dt.timedelta(days=j), 'Note': 0}
                    st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=True)
                st.rerun()
    
    # Planning Hebdo visuel
    cols = st.columns(7)
    for i, day in enumerate([dt.date.today() + dt.timedelta(days=i) for i in range(7)]):
        with cols[i]:
            st.markdown(f"**{day.strftime('%A %d')}**")
            for idx, r in df[df['Date'] == day].iterrows():
                st.write(f"ID {idx}: {r['Chapitre']} ({r['J_Type']})")
    
    st.markdown("---")
    st.subheader("✏️ Saisie des Notes par ID")
    id_s = st.number_input("Entrez l'ID de la ligne", 0, len(st.session_state.data)-1 if not st.session_state.data.empty else 0)
    if not st.session_state.data.empty and id_s in st.session_state.data.index:
        r = st.session_state.data.loc[id_s]
        st.info(f"Modifier {r['Chapitre']} ({r['J_Type']}) de {r['Matiere']}")
        note = st.number_input("Note", 0, 20, int(r['Note']))
        if st.button("Enregistrer"):
            st.session_state.data.loc[id_s, 'Note'] = note
            st.rerun()

elif page == "Graphiques":
    st.title("📊 Progression par Chapitre")
    if not df.empty:
        # Moyenne globale par chapitre (regroupe tous les J)
        stats = df[df['Note'] > 0].groupby('Chapitre')['Note'].mean()
        st.bar_chart(stats)
