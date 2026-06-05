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
            # Correctif Date : Conversion normalisée sans décalage
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
        try: v = float(str(row['Note']).replace(',', '.'))
        except: v = 0
        j_str = str(row['J_Type']).replace('J', '')
        seuil = int(st.session_state.config['seuils'].get(j_str, 12))
        return v > 0 and v < seuil and row['Statut'] != 'Traité'
   
    rattrapages = df_dos[df_dos.apply(est_en_rattrapage, axis=1)]
    if not rattrapages.empty:
        st.table(rattrapages[['Matiere', 'Chapitre', 'J_Type', 'Date', 'Note']])
        for _, row in rattrapages.iterrows():
            if st.button(f"Réintégrer {row['Chapitre']}", key=f"btn_{row['ID']}"):
                all_d = sorted(st.session_state.data[(st.session_state.data['Chapitre'] == row['Chapitre']) & (st.session_state.data['Dossier'] == choix_dos)]['Date'].unique())
                idx = all_d.index(row['Date'])
                if idx + 1 < len(all_d) and dt.date.today() < all_d[idx+1]:
                    new_r = row.copy()
                    new_r['ID'], new_r['Chapitre'] = str(uuid.uuid4()), f"{row['Chapitre']} RAP"
                    new_r['Date'], new_r['Statut'], new_r['Note'] = dt.date.today(), 'À faire', 0
                    st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_r])], ignore_index=True)
                    st.session_state.data.loc[st.session_state.data['ID'] == row['ID'], 'Statut'] = 'Traité'
                    save_all_to_sheet(st.session_state.data, st.session_state.config)
                    st.session_state.data, st.session_state.config = load_data_from_sheet()
                    st.rerun()
                else:
                    st.error("❌ Impossible : pas de place avant échéance suivante.")
                    st.session_state.data.loc[st.session_state.data['ID'] == row['ID'], 'Statut'] = 'Traité'
                    save_all_to_sheet(st.session_state.data, st.session_state.config)
                    if st.button("OK, supprimer"): st.rerun()

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
                        dj = d0 + dt.timedelta(days=j)
                        if dj <= dex: new_rows.append({'ID': str(uuid.uuid4()), 'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': f'J{j}', 'Date': dj, 'Note': 0, 'Statut': 'À faire'})
                    st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame(new_rows)])
                    save_all_to_sheet(st.session_state.data, st.session_state.config)
                    st.session_state.data, st.session_state.config = load_data_from_sheet()
                    st.rerun()

    st.subheader("🗓️ Planning Hebdomadaire")
    cols = st.columns(7)
    today = dt.date.today()
    start = today - dt.timedelta(days=today.weekday())
    for i, col in enumerate(cols):
        day = start + dt.timedelta(days=i)
        with col:
            st.markdown(f"**{day.strftime('%d/%m')}**")
            temp = st.session_state.data[(st.session_state.data['Date'] == day) & (st.session_state.data['Dossier'] == choix_dos)]
            for _, r in temp.iterrows():
                if st.checkbox(f"{r['Chapitre']} ({r['J_Type']})", value=(r['Statut'] == 'Fait'), key=f"chk_{r['ID']}"):
                    st.session_state.data.loc[st.session_state.data['ID'] == r['ID'], 'Statut'] = 'Fait'
                else: st.session_state.data.loc[st.session_state.data['ID'] == r['ID'], 'Statut'] = 'À faire'
    
    st.subheader("Saisie Notes (Journée)")
    df_t = st.session_state.data[(st.session_state.data['Date'] == dt.date.today()) & (st.session_state.data['Dossier'] == choix_dos)].copy()
    if not df_t.empty:
        temp_notes = {}
        for idx, row in df_t.iterrows():
            temp_notes[row['ID']] = st.text_input(f"{row['Chapitre']} ({row['J_Type']})", value=str(row['Note']), key=f"saisie_{row['ID']}")
        if st.button("💾 Enregistrer Notes"):
            for id_row, val in temp_notes.items():
                st.session_state.data.loc[st.session_state.data['ID'] == id_row, 'Note'] = val
            save_all_to_sheet(st.session_state.data, st.session_state.config)
            st.session_state.data, st.session_state.config = load_data_from_sheet()
            st.rerun()

elif page == "Graphiques":
    sel_chap = st.selectbox("Chapitre", st.session_state.data['Chapitre'].unique())
    df_n = st.session_state.data[st.session_state.data['Chapitre'] == sel_chap].copy()
    df_n['Note_Num'] = pd.to_numeric(df_n['Note'].astype(str).str.replace(',', '.'), errors='coerce')
    df_n['Order'] = df_n['J_Type'].str.extract('(\d+)').fillna(0).astype(int)
    st.altair_chart(alt.Chart(df_n.sort_values('Order')).mark_line(point=True).encode(x='J_Type', y='Note_Num'), use_container_width=True)