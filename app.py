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
    return pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note', 'Statut', 'Date_Examen', 'ID'])

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

# --- CALLBACKS POUR NETTOYAGE ---
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
    df_dos = st.session_state.data[st.session_state.data['Dossier'] == choix_dos]
    rattrapages = df_dos[df_dos.apply(lambda row: (row['Note'] > 0 and row['Note'] < int(st.session_state.config['seuils'].get(str(row['J_Type']).replace('J', ''), 12))), axis=1)]
    if not rattrapages.empty:
        st.table(rattrapages[['Matiere', 'Chapitre', 'J_Type', 'Date', 'Note']])
        for _, row in rattrapages.iterrows():
            if st.button(f"Réintégrer {row['Chapitre']}", key=f"btn_{row['ID']}"):
                d = dt.date.today(); dt_tr = d + dt.timedelta(days=1)
                n_r = {'ID':str(uuid.uuid4()),'Dossier':choix_dos,'Matiere':row['Matiere'],'Chapitre':row['Chapitre'],'J_Type':'RAP','Date':str(dt_tr),'Note':0,'Statut':'À faire'}
                st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([n_r])]); st.session_state.data = st.session_state.data[st.session_state.data['ID'] != row['ID']]; save_data(st.session_state.data); st.rerun()
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
                if dex:
                    new_rows = []
                    for j in [0] + st.session_state.config['cadencier']:
                        date_j = d0 + dt.timedelta(days=j)
                        if date_j <= dex:
                            new_rows.append({'ID': str(uuid.uuid4()), 'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': f'J{j}', 'Date': str(date_j), 'Note': 0, 'Statut': 'À faire'})
                    st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame(new_rows)])
                    save_data(st.session_state.data); st.rerun()

    st.subheader("🗓️ Planning Hebdomadaire")
    cols = st.columns(7)
    jours = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
    today = dt.date.today()
    start_week = today - dt.timedelta(days=today.weekday())
    for i, col in enumerate(cols):
        day = start_week + dt.timedelta(days=i)
        with col:
            st.markdown(f"**{jours[i]}**\n{day.strftime('%d/%m')}")
            temp_df = st.session_state.data.copy()
            df_day = temp_df[(pd.to_datetime(temp_df['Date']).dt.date == day) & (temp_df['Dossier'] == choix_dos)]
            for idx, r in df_day.iterrows():
                box_color = "🟢" if r['Statut'] == 'Fait' else "⚪"
                with st.popover(f"{box_color} {r['Chapitre']} ({r['J_Type']})"):
                    new_date = st.date_input("Date", value=r['Date'], key=f"d_{r['ID']}")
                    is_done_new = st.checkbox("Fait", value=(r['Statut'] == 'Fait'), key=f"c_{r['ID']}")
                    if st.button("Valider", key=f"b_{r['ID']}"):
                        st.session_state.data.at[idx, 'Date'] = new_date
                        st.session_state.data.at[idx, 'Statut'] = 'Fait' if is_done_new else 'À faire'
                        save_data(st.session_state.data); st.rerun()

    st.divider()
    st.subheader("Saisie Notes - Aujourd'hui")
    df_today = st.session_state.data[(pd.to_datetime(st.session_state.data['Date']).dt.date == today) & (st.session_state.data['Dossier'] == choix_dos)]
    if not df_today.empty:
        edited = st.data_editor(df_today[['ID', 'Chapitre', 'J_Type', 'Statut', 'Note']], column_config={"ID": None}, hide_index=True, use_container_width=True)
        if st.button("💾 Enregistrer Notes"):
            for _, row in edited.iterrows():
                mask = st.session_state.data['ID'] == row['ID']
                st.session_state.data.loc[mask, 'Note'] = row['Note']
                st.session_state.data.loc[mask, 'Statut'] = row['Statut']
            save_data(st.session_state.data); st.rerun()

# --- GRAPHIQUES ---
elif page == "Graphiques":
    st.title("📊 Analyse de Progression")
    mat_list = st.session_state.config['dossiers'].get(choix_dos, [])
    if mat_list:
        mat_sel = st.selectbox("Matière", mat_list)
        chap_list = st.session_state.data[(st.session_state.data['Dossier'] == choix_dos) & (st.session_state.data['Matiere'] == mat_sel)]['Chapitre'].unique()
        if chap_list.size > 0:
            chap_sel = st.selectbox("Chapitre", chap_list)
            df_c = st.session_state.data[(st.session_state.data['Dossier'] == choix_dos) & (st.session_state.data['Chapitre'] == chap_sel) & (st.session_state.data['Note'] > 0)]
            if not df_c.empty:
                fig = go.Figure([go.Scatter(x=df_c['J_Type'], y=df_c['Note'], mode='lines+markers')])
                fig.update_layout(yaxis=dict(range=[0, 20])); st.plotly_chart(fig, use_container_width=True)
            st.table(df_c[['J_Type', 'Date', 'Note']])