import streamlit as st
import pandas as pd
import datetime as dt
import uuid
import requests
import json
import altair as alt

st.set_page_config(layout="wide")

WEB_APP_URL = "https://script.google.com/macros/s/AKfycbwA7ZGCqHcDgw_Ia2PDjuvLqGDx1smoqR75VOo5IytV-QgMIw2_6xnZtXI1sFensDDwfw/exec"

def load_data_from_sheet():
    try:
        response = requests.get(WEB_APP_URL, timeout=15)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data.get('data', []), columns=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note', 'Statut', 'ID'])
            # Correction : Normalisation forcée pour éviter le décalage de jour
            df['Date'] = pd.to_datetime(df['Date']).dt.normalize().dt.date
            config = data.get('config', {'cours_max': 5, 'cadencier': [1, 3, 7, 14, 30], 'seuils': {'1': 12, '3': 12, '7': 14, '14': 14, '30': 16}, 'dossiers': {"PASS": []}})
            return df, config
    except: pass
    return pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note', 'Statut', 'ID']), {'cours_max': 5, 'cadencier': [1, 3, 7, 14, 30], 'seuils': {'1': 12, '3': 12, '7': 14, '14': 14, '30': 16}, 'dossiers': {"PASS": []}}

def save_all_to_sheet(df, config):
    df_to_send = df.copy()
    df_to_send['Date'] = df_to_send['Date'].astype(str)
    df_to_send['Note'] = df_to_send['Note'].astype(str)
    payload = {"data": df_to_send.values.tolist(), "config": config}
    try:
        requests.post(WEB_APP_URL, json=payload, timeout=15)
    except: st.error("Erreur de sauvegarde")

if 'data' not in st.session_state:
    st.session_state.data, st.session_state.config = load_data_from_sheet()

def reset_dossier():
    nom = st.session_state.d_in
    if nom and nom not in st.session_state.config['dossiers']:
        st.session_state.config['dossiers'][nom] = []
        save_all_to_sheet(st.session_state.data, st.session_state.config)
        st.session_state.data, st.session_state.config = load_data_from_sheet()
    st.session_state.d_in = ""

def reset_matiere():
    nom = st.session_state.m_in
    if nom and nom not in st.session_state.config['dossiers'][choix_dos]:
        st.session_state.config['dossiers'][choix_dos].append(nom)
        save_all_to_sheet(st.session_state.data, st.session_state.config)
        st.session_state.data, st.session_state.config = load_data_from_sheet()
    st.session_state.m_in = ""

st.sidebar.title("⚙️ Pilot Expert")
with st.sidebar.expander("🛠️ Réglages", expanded=False):
    st.session_state.config['cours_max'] = st.number_input("Max cours/jour", 1, 20, st.session_state.config.get('cours_max', 5))
    cad_str = st.text_input("Cadencier (jours)", ",".join(map(str, st.session_state.config['cadencier'])))
    st.session_state.config['cadencier'] = [int(x.strip()) for x in cad_str.split(",")]
    for j in st.session_state.config['cadencier']:
        st.session_state.config['seuils'][str(j)] = st.slider(f"Seuil Note J{j}", 10, 20, int(st.session_state.config['seuils'].get(str(j), 12)))
    if st.button("💾 Enregistrer"):
        save_all_to_sheet(st.session_state.data, st.session_state.config)
        st.rerun()

st.sidebar.text_input("Nouveau Dossier", key="d_in")
st.sidebar.button("➕ Créer Dossier", on_click=reset_dossier)
choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.config['dossiers'].keys()))
st.sidebar.text_input("Nom Matière", key="m_in")
st.sidebar.button("➕ Ajouter Matière", on_click=reset_matiere)
page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])

if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    if st.button("❌ Supprimer ce Dossier"):
        del st.session_state.config['dossiers'][choix_dos]
        st.session_state.data = st.session_state.data[st.session_state.data['Dossier'] != choix_dos]
        save_all_to_sheet(st.session_state.data, st.session_state.config)
        st.rerun()
    for m in st.session_state.config['dossiers'].get(choix_dos, []):
        with st.expander(f"📚 {m}"):
            c1, c2 = st.columns([4, 1])
            if c2.button("🗑️ Supprimer", key=f"del_{m}"):
                st.session_state.config['dossiers'][choix_dos].remove(m)
                st.session_state.data = st.session_state.data[(st.session_state.data['Dossier'] != choix_dos) | (st.session_state.data['Matiere'] != m)]
                save_all_to_sheet(st.session_state.data, st.session_state.config)
                st.rerun()
            chapitres_matiere = st.session_state.data[(st.session_state.data['Dossier'] == choix_dos) & (st.session_state.data['Matiere'] == m)]['Chapitre'].unique()
            if len(chapitres_matiere) > 0: st.write("**Chapitres :**", ", ".join(chapitres_matiere))

    st.subheader("⚠️ Rattrapages à traiter")
    df_dos = st.session_state.data[st.session_state.data['Dossier'] == choix_dos].copy()
    def est_en_rattrapage(row):
        try: valeur_note = float(str(row['Note']).replace(',', '.'))
        except: valeur_note = 0
        j_str = str(row['J_Type']).replace('J', '')
        seuil = int(st.session_state.config['seuils'].get(j_str, 12))
        return valeur_note > 0 and valeur_note < seuil and row['Statut'] != 'Traité'
   
    rattrapages = df_dos[df_dos.apply(est_en_rattrapage, axis=1)]
    if not rattrapages.empty:
        st.table(rattrapages[['Matiere', 'Chapitre', 'J_Type', 'Date', 'Note']])
        for _, row in rattrapages.iterrows():
            if st.button(f"Réintégrer {row['Chapitre']} ({row['J_Type']})", key=f"btn_{row['ID']}"):
                # Logique de contrôle de fenêtre temporelle
                all_dates = sorted(st.session_state.data[(st.session_state.data['Chapitre'] == row['Chapitre']) & (st.session_state.data['Dossier'] == choix_dos)]['Date'].unique())
                idx = all_dates.index(row['Date'])
                if idx + 1 < len(all_dates) and dt.date.today() < all_dates[idx+1]:
                    st.session_state.data.loc[st.session_state.data['ID'] == row['ID'], 'Statut'] = 'Traité'
                    save_all_to_sheet(st.session_state.data, st.session_state.config)
                    st.session_state.data, st.session_state.config = load_data_from_sheet()
                    st.rerun()
                else:
                    st.error(f"❌ Impossible de réintégrer : la date limite ({all_dates[idx+1] if idx+1 < len(all_dates) else 'inconnue'}) est dépassée.")
                    if st.button("Compris", key=f"ack_{row['ID']}"): st.rerun()

elif page == "Planning & Saisie":
    with st.expander("✍️ Ajouter Chapitre", expanded=True):
        with st.form("Add_Form", clear_on_submit=True):
            mat = st.selectbox("Matière", st.session_state.config['dossiers'].get(choix_dos, []))
            chap = st.text_input("Titre")
            d0 = st.date_input("Date J0", value=dt.date.today())
            dex = st.date_input("Date Examen", value=None)
            if st.form_submit_button("Générer Planning"):
                if chap and dex:
                    new_rows = [{'ID': str(uuid.uuid4()), 'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': 'J0', 'Date': d0, 'Note': 0, 'Statut': 'À faire'}]
                    for j in st.session_state.config['cadencier']:
                        d_j = d0 + dt.timedelta(days=j)
                        if d_j <= dex: new_rows.append({'ID': str(uuid.uuid4()), 'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': f'J{j}', 'Date': d_j, 'Note': 0, 'Statut': 'À faire'})
                    st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame(new_rows)]).drop_duplicates(subset=['Dossier', 'Chapitre', 'J_Type', 'Date'])
                    save_all_to_sheet(st.session_state.data, st.session_state.config)
                    st.rerun()

    st.subheader("🗓️ Planning Hebdomadaire")
    cols = st.columns(7)
    today = dt.date.today()
    start = today - dt.timedelta(days=today.weekday())
    for i, col in enumerate(cols):
        day = start + dt.timedelta(days=i)
        with col:
            st.markdown(f"**{day.strftime('%d/%m')}**")
            temp = st.session_state.data[(pd.to_datetime(st.session_state.data['Date']).dt.date == day) & (st.session_state.data['Dossier'] == choix_dos)]
            for _, r in temp.iterrows():
                c1, c2 = st.columns([0.8, 0.2])
                with c1:
                    if st.checkbox(f"{r['Chapitre']} ({r['J_Type']})", value=(r['Statut'] == 'Fait'), key=f"chk_{r['ID']}"):
                        st.session_state.data.loc[st.session_state.data['ID'] == r['ID'], 'Statut'] = 'Fait'
                    else:
                        st.session_state.data.loc[st.session_state.data['ID'] == r['ID'], 'Statut'] = 'À faire'
                with c2:
                    st.date_input("", value=r['Date'], key=f"cal_{r['ID']}", label_visibility="collapsed")
   
    st.subheader("Saisie Notes (Journée)")
    df_t = st.session_state.data[(pd.to_datetime(st.session_state.data['Date']).dt.date == dt.date.today()) & (st.session_state.data['Dossier'] == choix_dos)].copy()
   
    if not df_t.empty:
        temp_notes = {}
        for idx, row in df_t.iterrows():
            c1, c2 = st.columns([0.7, 0.3])
            c1.write(f"{row['Chapitre']} ({row['J_Type']})")
            temp_notes[row['ID']] = c2.text_input("Note (pts ; sép)", value=str(row['Note']), key=f"saisie_{row['ID']}")
           
        if st.button("💾 Enregistrer et Calculer Moyenne"):
            for id_row, val in temp_notes.items():
                if ';' in val:
                    try:
                        vals = [float(x.replace(',', '.').strip()) for x in val.split(';')]
                        st.session_state.data.loc[st.session_state.data['ID'] == id_row, 'Note'] = round(sum(vals)/len(vals), 1)
                    except: st.session_state.data.loc[st.session_state.data['ID'] == id_row, 'Note'] = val
                else:
                    st.session_state.data.loc[st.session_state.data['ID'] == id_row, 'Note'] = val.replace(',', '.')
            save_all_to_sheet(st.session_state.data, st.session_state.config)
            st.rerun()

elif page == "Graphiques":
    st.title("📊 Progression")
    matieres = st.session_state.config['dossiers'].get(choix_dos, [])
    sel_mat = st.selectbox("Choisir une matière", matieres)
    df_mat = st.session_state.data[(st.session_state.data['Dossier'] == choix_dos) & (st.session_state.data['Matiere'] == sel_mat)]
    chapitres = df_mat['Chapitre'].unique()
    if len(chapitres) > 0:
        sel_chap = st.selectbox("Choisir un chapitre", chapitres)
        df_notes = st.session_state.data[(st.session_state.data['Chapitre'] == sel_chap)].copy()
        df_notes['Note_Num'] = pd.to_numeric(df_notes['Note'].astype(str).str.replace(',', '.'), errors='coerce')
        df_notes['Order'] = df_notes['J_Type'].astype(str).str.extract('(\d+)').fillna(0).astype(int)
        df_notes = df_notes.sort_values(by='Order')
        chart = alt.Chart(df_notes).mark_line(point=True).encode(x='J_Type', y=alt.Y('Note_Num', scale=alt.Scale(domain=[0, 20])))
        st.altair_chart(chart, use_container_width=True)
