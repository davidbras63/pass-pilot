import streamlit as st
import pandas as pd
import datetime as dt
import os
import json
import uuid
import plotly.graph_objects as go

st.set_page_config(layout="wide")

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

# --- SIDEBAR ---
st.sidebar.title("⚙️ Pilot Expert")

if 'input_dossier' not in st.session_state: st.session_state.input_dossier = ""
if 'input_matiere' not in st.session_state: st.session_state.input_matiere = ""

def action_creer_dossier():
    nom = st.session_state.input_dossier
    if nom and nom not in st.session_state.config['dossiers']:
        st.session_state.config['dossiers'][nom] = []
        with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)
        st.session_state.input_dossier = ""

def action_ajouter_matiere():
    mat = st.session_state.input_matiere
    if mat and mat not in st.session_state.config['dossiers'][choix_dos]:
        st.session_state.config['dossiers'][choix_dos].append(mat)
        with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)
        st.session_state.input_matiere = ""

with st.sidebar.expander("🛠️ Réglages", expanded=False):
    st.session_state.config['cours_max'] = st.number_input("Max cours/jour", 1, 20, st.session_state.config.get('cours_max', 5))
    cad_str = st.text_input("Cadencier (jours)", ",".join(map(str, st.session_state.config['cadencier'])))
    st.session_state.config['cadencier'] = [int(x.strip()) for x in cad_str.split(",")]
    for j in st.session_state.config['cadencier']:
        st.session_state.config['seuils'][str(j)] = st.slider(f"Seuil Note J{j}", 10, 20, int(st.session_state.config['seuils'].get(str(j), 12)))
    if st.button("💾 Enregistrer"):
        with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)
        st.rerun()

st.sidebar.text_input("Nouveau Dossier", key="input_dossier")
st.sidebar.button("➕ Créer Dossier", on_click=action_creer_dossier)

dossiers_liste = list(st.session_state.config['dossiers'].keys())
if not dossiers_liste: st.stop()
choix_dos = st.sidebar.selectbox("Dossier", dossiers_liste)

st.sidebar.text_input("Nom Matière", key="input_matiere")
st.sidebar.button("➕ Ajouter Matière", on_click=action_ajouter_matiere)

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
        c1, c2 = st.columns([4, 1])
        c1.info(f"📚 {m}")
        if c2.button("🗑️", key=f"del_{m}"): st.session_state.config['dossiers'][choix_dos].remove(m); st.rerun()
    st.subheader("⚠️ Rattrapages à traiter")
    df_dos = st.session_state.data[st.session_state.data['Dossier'] == choix_dos].copy()
    # Filtre rattrapage : Note > 0, date passée, et en dessous du seuil
    rattrapages = df_dos[
        (df_dos['Note'] != "0") & 
        (pd.to_datetime(df_dos['Date']).dt.date <= dt.date.today()) &
        (df_dos.apply(lambda row: float(str(row['Note']).split(',')[0]) < int(st.session_state.config['seuils'].get(str(row['J_Type']).replace('J', '').replace('RAP', '1'), 12)), axis=1))
    ]
    if not rattrapages.empty:
        st.table(rattrapages[['Matiere', 'Chapitre', 'J_Type', 'Date', 'Note']])
        for _, row in rattrapages.iterrows():
            if st.button(f"Réintégrer {row['Chapitre']}", key=f"btn_{row['ID']}"):
                limite = dt.date.today() + dt.timedelta(days=15)
                dt_tr = None
                for i in range(1, 16):
                    t = dt.date.today() + dt.timedelta(days=i)
                    if len(st.session_state.data[(pd.to_datetime(st.session_state.data['Date']).dt.date == t) & (st.session_state.data['Dossier'] == choix_dos)]) < st.session_state.config.get('cours_max', 5):
                        dt_tr = t; break
                if dt_tr:
                    n_r = {'ID':str(uuid.uuid4()),'Dossier':choix_dos,'Matiere':row['Matiere'],'Chapitre':row['Chapitre'],'J_Type':'RAP','Date':dt_tr,'Note':'0','Statut':'À faire'}
                    st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([n_r])]); save_data(st.session_state.data); st.rerun()
    else: st.write("Aucun rattrapage en attente.")

# --- PLANNING & SAISIE ---
elif page == "Planning & Saisie":
    with st.expander("✍️ Ajouter Chapitre", expanded=False):
        with st.form("Add_Form", clear_on_submit=True):
            mat = st.selectbox("Matière", st.session_state.config['dossiers'].get(choix_dos, []))
            chap = st.text_input("Titre")
            d0 = st.date_input("Date J0")
            dex = st.date_input("Date Examen", value=None)
            if st.form_submit_button("Générer Planning"):
                # Vérification stricte : aucun chapitre du même nom dans le dossier
                if chap and not ((st.session_state.data['Chapitre'] == chap) & (st.session_state.data['Dossier'] == choix_dos)).any():
                    new_rows = [{'ID': str(uuid.uuid4()), 'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': 'J0', 'Date': d0, 'Note': '0', 'Statut': 'À faire'}]
                    for j in st.session_state.config['cadencier']:
                        date_j = d0 + dt.timedelta(days=j)
                        if dex and date_j <= dex:
                            new_rows.append({'ID': str(uuid.uuid4()), 'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': f'J{j}', 'Date': date_j, 'Note': '0', 'Statut': 'À faire'})
                    st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame(new_rows)])
                    save_data(st.session_state.data); st.rerun()
                else: st.error("Doublon : Ce chapitre existe déjà.")

    st.subheader("🗓️ Planning Hebdomadaire")
    cols = st.columns(7)
    jours = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
    today = dt.date.today()
    start_week = today - dt.timedelta(days=today.weekday())
    for i, col in enumerate(cols):
        day = start_week + dt.timedelta(days=i)
        with col:
            st.markdown(f"**{jours[i]}**\n{day.strftime('%d/%m')}")
            df_day = st.session_state.data[(pd.to_datetime(st.session_state.data['Date']).dt.date == day) & (st.session_state.data['Dossier'] == choix_dos)]
            for idx, r in df_day.iterrows():
                with st.popover(f"{r['Chapitre']} ({r['J_Type']})"):
                    if st.button("Valider", key=f"val_{r['ID']}"): st.session_state.data.at[idx, 'Statut'] = 'Fait'; save_data(st.session_state.data); st.rerun()

    st.divider()
    st.subheader("Saisie Notes - Aujourd'hui")
    df_today = st.session_state.data[(pd.to_datetime(st.session_state.data['Date']).dt.date == today) & (st.session_state.data['Dossier'] == choix_dos)]
    if not df_today.empty:
        chap_sel = st.selectbox("Sélectionner Chapitre", df_today['Chapitre'].unique())
        row = df_today[df_today['Chapitre'] == chap_sel].iloc[0]
        n_input = st.number_input("Nouvelle Note", 0.0, 20.0, 0.0)
        if st.button("Ajouter Note"):
            actuel = str(row['Note'])
            new_note = str(n_input) if actuel == "0" else actuel + "," + str(n_input)
            st.session_state.data.loc[st.session_state.data['ID'] == row['ID'], 'Note'] = new_note
            save_data(st.session_state.data); st.rerun()
        st.info(f"Notes actuelles : {row['Note']}")

# --- GRAPHIQUES ---
elif page == "Graphiques":
    st.title("📊 Analyse de Progression")
    mat_list = st.session_state.config['dossiers'].get(choix_dos, [])
    if mat_list:
        mat_sel = st.selectbox("Matière", mat_list)
        chap_list = st.session_state.data[(st.session_state.data['Dossier'] == choix_dos) & (st.session_state.data['Matiere'] == mat_sel)]['Chapitre'].unique()
        if len(chap_list) > 0:
            chap_sel = st.selectbox("Chapitre", chap_list)
            df_c = st.session_state.data[(st.session_state.data['Dossier'] == choix_dos) & (st.session_state.data['Chapitre'] == chap_sel)].copy()
            
            def moy(x): 
                notes = [float(n) for n in str(x).split(',') if n != '0']
                return sum(notes)/len(notes) if notes else 0
            df_c['Moyenne'] = df_c['Note'].apply(moy)
            
            # Affichage graphique si des notes existent
            df_plot = df_c[df_c['Moyenne'] > 0]
            if not df_plot.empty:
                fig = go.Figure([go.Scatter(x=df_plot['J_Type'], y=df_plot['Moyenne'], mode='lines+markers')])
                st.plotly_chart(fig)
            
            # Affichage tableau uniquement pour les entrées ayant des notes (exclut les '0')
            df_table = df_c[df_c['Note'] != "0"]
            if not df_table.empty:
                st.table(df_table[['Chapitre', 'J_Type', 'Date', 'Note']])