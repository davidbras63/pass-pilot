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
with st.sidebar.expander("🛠️ Réglages", expanded=False):
    st.session_state.config['cours_max'] = st.number_input("Max cours/jour", 1, 20, st.session_state.config.get('cours_max', 5))
    cad_str = st.text_input("Cadencier (jours)", ",".join(map(str, st.session_state.config['cadencier'])))
    st.session_state.config['cadencier'] = [int(x.strip()) for x in cad_str.split(",")]
    for j in st.session_state.config['cadencier']:
        st.session_state.config['seuils'][str(j)] = st.slider(f"Seuil Note J{j}", 10, 20, int(st.session_state.config['seuils'].get(str(j), 12)))
    if st.button("💾 Enregistrer"):
        with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)
        st.rerun()

nom_dossier = st.sidebar.text_input("Nouveau Dossier")
if st.sidebar.button("➕ Créer Dossier") and nom_dossier:
    st.session_state.config['dossiers'][nom_dossier] = []; st.rerun()

choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.config['dossiers'].keys()))
nom_matiere = st.sidebar.text_input("Nom Matière")
if st.sidebar.button("➕ Ajouter Matière") and nom_matiere:
    st.session_state.config['dossiers'][choix_dos].append(nom_matiere); st.rerun()

page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])

# --- DASHBOARD ---
if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    
    if st.button("❌ Supprimer ce Dossier"):
        del st.session_state.config['dossiers'][choix_dos]
        with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)
        st.rerun()
        
    for m in st.session_state.config['dossiers'].get(choix_dos, []):
        c1, c2 = st.columns([4, 1])
        c1.info(f"📚 {m}")
        if c2.button("🗑️", key=f"del_{m}"): st.session_state.config['dossiers'][choix_dos].remove(m); st.rerun()
   
    st.subheader("⚠️ Rattrapages à traiter")
    df_dos = st.session_state.data[st.session_state.data['Dossier'] == choix_dos]
    
    def est_en_rattrapage(row):
        j_str = row['J_Type'].replace('J', '')
        seuil = int(st.session_state.config['seuils'].get(j_str, 12))
        return row['Note'] > 0 and row['Note'] < seuil

    rattrapages = df_dos[df_dos.apply(est_en_rattrapage, axis=1)]
   
    if not rattrapages.empty:
        st.table(rattrapages[['Matiere', 'Chapitre', 'J_Type', 'Date', 'Note']])
        for _, row in rattrapages.iterrows():
            if st.button(f"Réintégrer {row['Chapitre']}", key=f"btn_{row['ID']}"):
                d = dt.date.today(); dt_tr = None
                for i in range(1, 15):
                    t = d + dt.timedelta(days=i)
                    if t.weekday() == 6: continue
                    nb = len(st.session_state.data[(pd.to_datetime(st.session_state.data['Date']).dt.date == t) & (st.session_state.data['Dossier'] == choix_dos)])
                    if nb < st.session_state.config.get('cours_max', 3): dt_tr = t; break
                if not dt_tr: dt_tr = d + dt.timedelta(days=1)
                n_r = {'ID':str(uuid.uuid4()),'Dossier':choix_dos,'Matiere':row['Matiere'],'Chapitre':row['Chapitre'],'J_Type':'RAP','Date':str(dt_tr),'Note':0,'Statut':'À faire'}
                st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([n_r])]); st.session_state.data = st.session_state.data[st.session_state.data['ID'] != row['ID']]; save_data(st.session_state.data); st.rerun()
    else:
        st.write("Aucun rattrapage en attente.")

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
                    st.session_state.data = st.session_state.data.drop_duplicates(subset=['Dossier', 'Chapitre', 'J_Type', 'Date'], keep='first')
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
            temp_df['Date_Obj'] = pd.to_datetime(temp_df['Date']).dt.date
            df_day = temp_df[(temp_df['Date_Obj'] == day) & (temp_df['Dossier'] == choix_dos)]
            for _, r in df_day.iterrows(): st.caption(f"{r['Chapitre']} ({r['J_Type']})")

    st.divider()
    st.subheader(f"Saisie Notes - Aujourd'hui")
    temp_df = st.session_state.data.copy()
    temp_df['Date_Obj'] = pd.to_datetime(temp_df['Date']).dt.date
    df_today = temp_df[(temp_df['Date_Obj'] == today) & (temp_df['Dossier'] == choix_dos)].copy()
    if not df_today.empty:
        edited = st.data_editor(df_today[['ID', 'Chapitre', 'J_Type', 'Statut', 'Note']], column_config={"ID": None}, hide_index=True, use_container_width=True)
        if st.button("💾 Enregistrer"):
            for _, row in edited.iterrows():
                mask = st.session_state.data['ID'] == row['ID']
                st.session_state.data.loc[mask, 'Note'] = row['Note']
                st.session_state.data.loc[mask, 'Statut'] = row['Statut']
            save_data(st.session_state.data)
            st.success("Notes enregistrées avec succès !")
            st.session_state.page = "Dashboard"; st.rerun()
    else:
        st.info("Aucun chapitre prévu aujourd'hui.")

# --- GRAPHIQUES ---
elif page == "Graphiques":
    st.title("📊 Analyse de Progression")
    
    matieres_dispos = st.session_state.config['dossiers'].get(choix_dos, [])
    if not matieres_dispos:
        st.warning("Aucune matière créée dans ce dossier.")
    else:
        mat_sel = st.selectbox("Choisir une Matière", matieres_dispos)
        
        chapitres_dispos = st.session_state.data[
            (st.session_state.data['Dossier'] == choix_dos) & 
            (st.session_state.data['Matiere'] == mat_sel)
        ]['Chapitre'].unique()
        
        if len(chapitres_dispos) == 0:
            st.info("Aucun chapitre pour cette matière.")
        else:
            chap_sel = st.selectbox("Choisir un Chapitre", chapitres_dispos)
            
            df_chap = st.session_state.data[
                (st.session_state.data['Dossier'] == choix_dos) & 
                (st.session_state.data['Matiere'] == mat_sel) & 
                (st.session_state.data['Chapitre'] == chap_sel)
            ].sort_values('Date')

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_chap['J_Type'], y=df_chap['Note'],
                mode='lines+markers', name='Progression',
                line=dict(color='#00CC96', width=3)
            ))
            
            fig.update_layout(
                title=f"Progression : {chap_sel}",
                xaxis_title="Étapes (J)",
                yaxis_title="Note / 20",
                yaxis=dict(range=[0, 20]),
                template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)
            st.table(df_chap[['J_Type', 'Date', 'Note']])