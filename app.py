import streamlit as st
import pandas as pd
import datetime as dt
import os
import json

st.set_page_config(layout="wide")

DATA_FILE = "data.csv"
CONFIG_FILE = "config.json"

# --- RÉINITIALISATION AUTOMATIQUE ---
if os.path.exists(DATA_FILE):
    try:
        pd.read_csv(DATA_FILE)
    except:
        os.remove(DATA_FILE)

def load_data():
    cols = ['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note']
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
        df['Note'] = pd.to_numeric(df['Note'], errors='coerce').fillna(0)
        return df
    return pd.DataFrame(columns=cols)

def save_data(df): df.to_csv(DATA_FILE, index=False)

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f: return json.load(f)
        except: pass
    return {'cours_max': 5, 'cadencier': [1, 3, 7, 14, 30, 60, 90, 120], 'seuils': {'1': 12}, 'dossiers': {"PASS": []}}

if 'data' not in st.session_state: st.session_state.data = load_data()
if 'config' not in st.session_state: st.session_state.config = load_config()

# --- SIDEBAR ---
st.sidebar.title("⚙️ Pilot Expert")
with st.sidebar.expander("🛠️ Réglages", expanded=True):
    st.session_state.config['cours_max'] = st.number_input("Max cours/jour", 1, 20, st.session_state.config.get('cours_max', 5))
    cad_input = st.text_input("Cadencier", ",".join(map(str, st.session_state.config.get('cadencier', [1,3,7]))))
    st.session_state.config['cadencier'] = [int(x.strip()) for x in cad_input.split(",")]
    for j in st.session_state.config['cadencier']:
        st.session_state.config['seuils'][str(j)] = st.slider(f"Seuil J{j}", 10, 20, int(st.session_state.config['seuils'].get(str(j), 12)))
    if st.button("💾 Enregistrer"): 
        with open(CONFIG_FILE, "w") as f: json.dump(st.session_state.config, f)
        st.rerun()

choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.config['dossiers'].keys()))
if st.sidebar.button("➕ Créer Dossier"): st.session_state.config['dossiers'][st.sidebar.text_input("Nom")] = []; st.rerun()
if st.sidebar.button("➕ Ajouter Matière"): st.session_state.config['dossiers'][choix_dos].append(st.sidebar.text_input("Nom Matière")); st.rerun()

page = st.sidebar.radio("Navigation", ["Dashboard", "Planning & Saisie", "Graphiques"])
df = st.session_state.data[st.session_state.data['Dossier'] == choix_dos].copy()

# --- PAGES ---
if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    for m in st.session_state.config['dossiers'].get(choix_dos, []):
        c1, c2 = st.columns([4, 1])
        c1.info(f"📚 {m}")
        if c2.button("🗑️", key=f"del_{m}"): st.session_state.config['dossiers'][choix_dos].remove(m); st.rerun()
    
    st.subheader("⚠️ Rattrapages")
    if not df.empty:
        df['Note'] = pd.to_numeric(df['Note'], errors='coerce')
        rattrapages = df[(df['Note'] > 0) & (df['Note'] < 12)]
        if not rattrapages.empty:
            disp_df = rattrapages.copy()
            disp_df['Date'] = disp_df['Date'].apply(lambda x: x.strftime('%d/%m/%Y') if pd.notnull(x) else "")
            st.table(disp_df[['Matiere', 'Chapitre', 'J_Type', 'Date', 'Note']])

elif page == "Planning & Saisie":
    st.title("🗓️ Planning & Saisie")
    with st.expander("➕ Ajouter"):
        with st.form("Add"):
            mat = st.selectbox("Matière", st.session_state.config['dossiers'].get(choix_dos, []))
            chap = st.text_input("Nom")
            d0 = st.date_input("Date J0")
            ex = st.date_input("Date Examen", value=None)
            if st.form_submit_button("Générer"):
                if not ex: st.error("Date examen obligatoire !")
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
                    if st.button("Valider", key=f"b_{idx}"): st.rerun()

    st.subheader("📝 Saisie")
    df_today = df[df['Date'] == dt.date.today()]
    if not df_today.empty:
        edited = st.data_editor(df_today)
        if st.button("Enregistrer"): st.session_state.data.update(edited); save_data(st.session_state.data); st.rerun()

elif page == "Graphiques":
    st.title("📊 Progression")
    if not df.empty:
        df_clean = df[df['Note'] > 0].copy()
        if not df_clean.empty:
            df_clean['Date'] = df_clean['Date'].apply(lambda x: x.strftime('%d/%m/%Y'))
            st.line_chart(df_clean.pivot_table(index='Date', columns='Matiere', values='Note', aggfunc='mean'))