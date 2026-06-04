import streamlit as st
import pandas as pd
import datetime as dt
import os
import json
import uuid
import time
import altair as alt
import requests

st.set_page_config(layout="wide")

# --- SCRIPT DE CONNEXION GOOGLE APPS SCRIPT ---
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbyLNNVhU2B775oH7VW84dU2Ud4g88c2H1XA-M-PXyq2lpXYKZS7pwJW6Q2FiVjMjMZSbw/exec"

def load_data_from_sheet():
    """Récupère les données depuis le Google Sheet"""
    try:
        response = requests.get(WEB_APP_URL)
        data = response.json()
        return pd.DataFrame(data[1:], columns=data[0])
    except:
        return None

# --- RESTE DU CODE ORIGINAL ---

DATA_FILE = "data.csv"
CONFIG_FILE = "config.json"

# --- GESTION DONNÉES & CONFIG ---
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        return df.drop_duplicates()
    return pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note', 'Statut', 'ID'])

def save_data(df):
    df.drop_duplicates(inplace=True)
    df.to_csv(DATA_FILE, index=False)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f: return json.load(f)
    return {'cours_max': 5, 'cadencier': [1, 3, 7, 14, 30], 'seuils': {'1': 12, '3': 12, '7': 14, '14': 14, '30': 16}, 'dossiers': {"PASS": []}}

if 'data' not in st.session_state: st.session_state.data = load_data()
if 'config' not in st.session_state: st.session_state.config = load_config()

# --- FONCTIONS DE RÉINITIALISATION ---
def reset_dossier():
    nom = st.session_state.d_in
    if nom and nom not in st.session_state.config['dossiers']:
        st.session_state.config['dossiers'][nom] = []
        with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)
    st.session_state.d_in = ""

def reset_matiere():
    nom = st.session_state.m_in
    if nom and nom not in st.session_state.config['dossiers'][choix_dos]:
        st.session_state.config['dossiers'][choix_dos].append(nom)
        with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)
    st.session_state.m_in = ""

# --- SIDEBAR ---
st.sidebar.title("⚙️ Pilot Expert")

with st.sidebar.expander("🛠️ Réglages", expanded=False):
    st.session_state.config['cours_max'] = st.number_input("Max cours/jour", 1, 20, st.session_state.config.get('cours_max', 5))
    cad_str = st.text_input("Cadencier (jours)", ",".join(map(str, st.session_state.config['cadencier'])))
    st.session_state.config['cadencier'] = [int(x.strip()) for x in cad_str.split(",")]
    for j in st.session_state.config['cadencier']:
        st.session_state.config['seuils'][str(j)] = st.slider(f"Seuil Note J{j}", 10, 20, int(st.session_state.config['seuils'].get(str(j), 12)))
    if st.button("💾 Enregistrer"):
        with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)
        st.rerun()

st.sidebar.text_input("Nouveau Dossier", key="d_in")
st.sidebar.button("➕ Créer Dossier", on_click=reset_dossier)
choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.config['dossiers'].keys()))
st.sidebar.text_input("Nom Matière", key="m_in")
st.sidebar.button("➕ Ajouter Matière", on_click=reset_matiere)
page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])

# --- DASHBOARD ---
if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    if st.button("❌ Supprimer ce Dossier"):
        del st.session_state.config['dossiers'][choix_dos]
        with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)
        st.session_state.data = st.session_state.data[st.session_state.data['Dossier'] != choix_dos]
        save_data(st.session_state.data)
        st.rerun()
   
    for m in st.session_state.config['dossiers'].get(choix_dos, []):
        with st.expander(f"📚 {m}"):
            c1, c2 = st.columns([4, 1])
            if c2.button("🗑️ Supprimer cette matière", key=f"del_{m}"):
                st.session_state.config['dossiers'][choix_dos].remove(m)
                with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)
                st.session_state.data = st.session_state.data[(st.session_state.data['Dossier'] != choix_dos) | (st.session_state.data['Matiere'] != m)]
                save_data(st.session_state.data)
                st.rerun()
           
            chapitres_matiere = st.session_state.data[(st.session_state.data['Dossier'] == choix_dos) & (st.session_state.data['Matiere'] == m)]['Chapitre'].unique()
            if len(chapitres_matiere) > 0:
                st.write("**Chapitres enregistrés :**")
                st.write(", ".join(chapitres_matiere))
            else:
                st.info("Aucun chapitre dans cette matière.")

    st.subheader("⚠️ Rattrapages à traiter")
    df_dos = st.session_state.data[st.session_state.data['Dossier'] == choix_dos]
    def est_en_rattrapage(row):
        j_str = str(row['J_Type']).replace('J', '')
        seuil = int(st.session_state.config['seuils'].get(j_str, 12))
        return row['Note'] > 0 and row['Note'] < seuil and row['Statut'] != 'Traité'
   
    rattrapages = df_dos[df_dos.apply(est_en_rattrapage, axis=1)]
   
    if not rattrapages.empty:
        st.table(rattrapages[['Matiere', 'Chapitre', 'J_Type', 'Date', 'Note']])
        for _, row in rattrapages.iterrows():
            if st.button(f"Réintégrer {row['Chapitre']}", key=f"btn_{row['ID']}"):
                future_dates = st.session_state.data[(st.session_state.data['Chapitre'] == row['Chapitre']) & (st.session_state.data['Date'] > row['Date'])]['Date']
                date_limite = min(future_dates) if not future_dates.empty else None
                if date_limite:
                    date_candidat = dt.date.today() + dt.timedelta(days=1)
                    trouve = False
                    while date_candidat < date_limite and not trouve:
                        count = len(st.session_state.data[(pd.to_datetime(st.session_state.data['Date']).dt.date == date_candidat) & (st.session_state.data['Dossier'] == choix_dos)])
                        deja_occupe = date_candidat in st.session_state.data[st.session_state.data['Chapitre'] == row['Chapitre']]['Date'].tolist()
                        if not deja_occupe and date_candidat.weekday() != 6 and count < st.session_state.config.get('cours_max', 5):
                            trouve = True
                        else:
                            date_candidat += dt.timedelta(days=1)
                    if trouve:
                        n_r = {'ID': str(uuid.uuid4()), 'Dossier': choix_dos, 'Matiere': row['Matiere'], 'Chapitre': row['Chapitre'], 'J_Type': 'RAP', 'Date': date_candidat, 'Note': 0, 'Statut': 'À faire'}
                        st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([n_r])])
                        st.session_state.data.loc[st.session_state.data['ID'] == row['ID'], 'Statut'] = 'Traité'
                        save_data(st.session_state.data)
                        st.rerun()
                    else:
                        st.error("Rattrapage impossible avant le J suivant.")
                        time.sleep(2)
                        st.session_state.data.loc[st.session_state.data['ID'] == row['ID'], 'Statut'] = 'Traité'
                        save_data(st.session_state.data)
                        st.rerun()
                else:
                    st.error("Aucune échéance future trouvée.")
                    time.sleep(2)
                    st.session_state.data.loc[st.session_state.data['ID'] == row['ID'], 'Statut'] = 'Traité'
                    save_data(st.session_state.data)
                    st.rerun()

# --- PLANNING & SAISIE ---
elif page == "Planning & Saisie":
    with st.expander("✍️ Ajouter Chapitre", expanded=True):
        with st.form("Add_Form", clear_on_submit=True):
            mat = st.selectbox("Matière", st.session_state.config['dossiers'].get(choix_dos, []))
            chap = st.text_input("Titre")
            d0 = st.date_input("Date J0")
            dex = st.date_input("Date Examen", value=None)
            if st.form_submit_button("Générer Planning"):
                if chap and dex:
                    new_rows = [{'ID': str(uuid.uuid4()), 'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': 'J0', 'Date': d0, 'Note': 0, 'Statut': 'À faire'}]
                    for j in st.session_state.config['cadencier']:
                        d_j = d0 + dt.timedelta(days=j)
                        if d_j <= dex:
                            new_rows.append({'ID': str(uuid.uuid4()), 'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': f'J{j}', 'Date': d_j, 'Note': 0, 'Statut': 'À faire'})
                    st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame(new_rows)]).drop_duplicates(subset=['Dossier', 'Chapitre', 'J_Type', 'Date'])
                    save_data(st.session_state.data)
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
                c1, c2 = st.columns([0.1, 1])
                with c1:
                    with st.popover("🎯"):
                        nouvelle_date = st.date_input("Changer date :", r['Date'], key=f"d_{r['ID']}")
                        if st.button("Valider", key=f"btn_{r['ID']}"):
                            st.session_state.data.loc[st.session_state.data['ID'] == r['ID'], 'Date'] = nouvelle_date
                            save_data(st.session_state.data)
                            st.rerun()
                with c2:
                    est_fait = r['Statut'] == 'Fait'
                    if st.checkbox(f"{r['Chapitre']} ({r['J_Type']})", value=est_fait, key=f"chk_{r['ID']}"):
                        if not est_fait:
                            mask = st.session_state.data['ID'] == r['ID']
                            st.session_state.data.loc[mask, 'Statut'] = 'Fait'
                            save_data(st.session_state.data)
                            st.rerun()
                    else:
                        if est_fait:
                            mask = st.session_state.data['ID'] == r['ID']
                            st.session_state.data.loc[mask, 'Statut'] = 'À faire'
                            save_data(st.session_state.data)
                            st.rerun()

    st.divider()
    st.subheader("Saisie Notes - Aujourd'hui")
    df_t = st.session_state.data[(pd.to_datetime(st.session_state.data['Date']).dt.date == today) & (st.session_state.data['Dossier'] == choix_dos)].copy()
    if not df_t.empty:
        # CONVERSION CRUCIALE : Force la colonne Note en format texte
        df_t['Note'] = df_t['Note'].astype(str)
        
        edited = st.data_editor(df_t[['ID', 'Chapitre', 'J_Type', 'Note', 'Statut']], 
                                column_config={"ID": None, "Note": st.column_config.TextColumn("Note (ex: 12, 14)")}, 
                                use_container_width=True)
        if st.button("💾 Enregistrer"):
            for _, row in edited.iterrows():
                val_note = str(row['Note'])
                mask = st.session_state.data['ID'] == row['ID']
                if ',' in val_note:
                    try:
                        notes_list = [float(n.strip().replace(',', '.')) for n in val_note.split(',') if n.strip()]
                        moyenne = sum(notes_list) / len(notes_list)
                        st.session_state.data.loc[mask, ['Note', 'Statut']] = [round(moyenne, 1), row['Statut']]
                    except:
                        st.session_state.data.loc[mask, ['Note', 'Statut']] = [row['Note'], row['Statut']]
                else:
                    st.session_state.data.loc[mask, ['Note', 'Statut']] = [row['Note'], row['Statut']]
            save_data(st.session_state.data)
            st.rerun()

elif page == "Graphiques":
    st.title("📊 Progression")
    matieres = st.session_state.config['dossiers'].get(choix_dos, [])
    sel_mat = st.selectbox("Choisir une matière", matieres)
    df_mat = st.session_state.data[(st.session_state.data['Dossier'] == choix_dos) & (st.session_state.data['Matiere'] == sel_mat)]
    chapitres = df_mat['Chapitre'].unique()
    if len(chapitres) > 0:
        sel_chap = st.selectbox("Choisir un chapitre", chapitres)
        df_notes = st.session_state.data[(st.session_state.data['Dossier'] == choix_dos) & (st.session_state.data['Chapitre'] == sel_chap)].copy()
        df_notes['Note_Num'] = pd.to_numeric(df_notes['Note'], errors='coerce')
        if not df_notes.empty:
            df_notes['Order'] = df_notes['J_Type'].astype(str).str.extract('(\d+)').fillna(0).astype(int)
            df_notes = df_notes.sort_values(by='Order')
            chart = alt.Chart(df_notes).mark_line(point=True, strokeWidth=2).encode(
                x=alt.X('J_Type', sort=None, title="Jours de révision"),
                y=alt.Y('Note_Num', scale=alt.Scale(domain=[0, 20]), title="Note"),
                tooltip=['J_Type', 'Note_Num']
            ).properties(width=400, height=250)
            st.altair_chart(chart, use_container_width=False)
        else:
            st.warning("Aucune donnée trouvée pour ce chapitre.")
    else:
        st.info("Aucun chapitre trouvé pour cette matière.")