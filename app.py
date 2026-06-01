import streamlit as st
import pandas as pd
import datetime as dt
import os
import json

st.set_page_config(layout="wide")

DATA_FILE = "data.csv"
CONFIG_FILE = "config.json"

# --- CHARGEMENT ---
def load_data():
    cols = ['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note']
    if os.path.exists(DATA_FILE):
        # On force la lecture des dates en français
        df = pd.read_csv(DATA_FILE)
        df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce').dt.date
        df['Note'] = pd.to_numeric(df['Note'], errors='coerce').fillna(0)
        return df
    return pd.DataFrame(columns=cols)

def save_data(df): df.to_csv(DATA_FILE, index=False)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f: return json.load(f)
    return {'cadencier': [1, 3, 7, 14, 30, 60, 90, 120], 
            'seuils': {'1': 12, '3': 12, '7': 14, '14': 14, '30': 16, '60': 16, '90': 18, '120': 18},
            'dossiers': {"PASS": []}}

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f: json.dump(cfg, f)

if 'data' not in st.session_state: st.session_state.data = load_data()
if 'config' not in st.session_state: st.session_state.config = load_config()

# --- SIDEBAR ---
st.sidebar.title("⚙️ Pilot Expert")

with st.sidebar.expander("🛠️ Réglages Seuils"):
    cad_str = ",".join(map(str, st.session_state.config.get('cadencier', [1,3,7])))
    cad_input = st.text_input("Cadencier (jours)", cad_str)
    st.session_state.config['cadencier'] = [int(x.strip()) for x in cad_input.split(",")]
    for j in st.session_state.config['cadencier']:
        st.session_state.config['seuils'][str(j)] = st.slider(f"Seuil J{j}", 10, 20, int(st.session_state.config['seuils'].get(str(j), 12)))
    if st.button("💾 Enregistrer"): save_config(st.session_state.config); st.rerun()

new_folder = st.sidebar.text_input("Nouveau Dossier")
if st.sidebar.button("➕ Créer Dossier") and new_folder:
    st.session_state.config['dossiers'][new_folder] = []; save_config(st.session_state.config); st.rerun()

choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.config['dossiers'].keys()))
new_mat = st.sidebar.text_input("Ajouter Matière")
if st.sidebar.button("➕ Ajouter Matière") and new_mat:
    st.session_state.config['dossiers'][choix_dos].append(new_mat); save_config(st.session_state.config); st.rerun()

page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])
df = st.session_state.data[st.session_state.data['Dossier'] == choix_dos].copy()

# --- PAGES ---
if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    for m in st.session_state.config['dossiers'].get(choix_dos, []):
        c1, c2 = st.columns([4, 1])
        c1.info(f"📚 {m}")
        if c2.button("🗑️", key=f"del_{m}"):
            st.session_state.config['dossiers'][choix_dos].remove(m); save_config(st.session_state.config); st.rerun()
    
    st.subheader("⚠️ Tableau des Rattrapages")
    rattrapages = pd.DataFrame()
    for j in st.session_state.config['cadencier']:
        mask = (df['J_Type'] == f"J{j}") & (df['Note'] > 0) & (df['Note'] < st.session_state.config['seuils'].get(str(j), 12))
        rattrapages = pd.concat([rattrapages, df[mask]])
    # Formatage date français pour l'affichage
    if not rattrapages.empty:
        rattrapages['Date'] = rattrapages['Date'].apply(lambda x: x.strftime('%d/%m/%Y'))
        st.table(rattrapages[['Matiere', 'Chapitre', 'J_Type', 'Date', 'Note']])

elif page == "Planning & Saisie":
    st.title("🗓️ Planning & Saisie")
    with st.expander("➕ Ajouter Chapitre"):
        with st.form("Add"):
            mat = st.selectbox("Matière", st.session_state.config['dossiers'].get(choix_dos, []))
            chap = st.text_input("Chapitre")
            d0 = st.date_input("Date J0")
            ex = st.date_input("Date Examen (Obligatoire)", value=None)
            if st.form_submit_button("Générer"):
                if not ex: st.error("La date d'examen est obligatoire !")
                else:
                    for j in [0] + st.session_state.config['cadencier']:
                        d = d0 + dt.timedelta(days=j)
                        if d <= ex:
                            new_row = {'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': f"J{j}", 'Date': d, 'Note': 0}
                            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=True)
                    save_data(st.session_state.data); st.rerun()

    st.subheader("Planning Visuel")
    cols = st.columns(7)
    for i, day in enumerate([dt.date.today() + dt.timedelta(days=x) for x in range(7)]):
        with cols[i]:
            st.markdown(f"**{day.strftime('%d/%m')}**")
            for idx, r in df[df['Date'] == day].iterrows():
                with st.expander(f"{r['Matiere']} ({r['J_Type']})"):
                    new_d = st.date_input("Décaler", r['Date'], key=f"d_{idx}")
                    if st.button("Valider", key=f"b_{idx}"):
                        st.session_state.data.at[idx, 'Date'] = new_d
                        save_data(st.session_state.data); st.rerun()

    st.subheader("📝 Saisie")
    df_today = df[df['Date'] == dt.date.today()]
    if not df_today.empty:
        edited = st.data_editor(df_today)
        if st.button("Enregistrer"): st.session_state.data.update(edited); save_data(st.session_state.data); st.rerun()

elif page == "Graphiques":
    st.title("📊 Progression")
    if not df.empty:
        df_clean = df[df['Note'] > 0].copy()
        df_clean['Date'] = df_clean['Date'].astype(str) # Force format pour graph
        st.line_chart(df_clean.pivot(index='Date', columns='Matiere', values='Note'))