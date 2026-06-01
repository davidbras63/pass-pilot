import streamlit as st
import pandas as pd
import datetime as dt
import os
import json

st.set_page_config(layout="wide")

DATA_FILE = "data.csv"
CONFIG_FILE = "config.json"

# --- GESTION DONNÉES & CONFIG ---
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        return df.drop_duplicates()
    return pd.DataFrame(columns=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note', 'Statut', 'Date_Examen'])

def save_data(df):
    df.drop_duplicates(inplace=True)
    df.to_csv(DATA_FILE, index=False)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f: return json.load(f)
    return {'cours_max': 5, 'cadencier': [1, 3, 7, 14, 30], 'seuils': {1: 12, 3: 12, 7: 14, 14: 14, 30: 16}, 'dossiers': {"PASS": []}}

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
    for m in st.session_state.config['dossiers'].get(choix_dos, []):
        c1, c2 = st.columns([4, 1])
        c1.info(f"📚 {m}")
        if c2.button("🗑️", key=f"del_{m}"): st.session_state.config['dossiers'][choix_dos].remove(m); st.rerun()
    
    st.subheader("⚠️ Rattrapages")
# On récupère les données de ce dossier
df_dos = st.session_state.data[st.session_state.data['Dossier'] == choix_dos]
# On filtre les notes à rattraper (note entre 1 et 11 par exemple)
rattrapages = df_dos[(df_dos['Note'] > 0) & (df_dos['Note'] < 12)]

if not rattrapages.empty:
    # --- LA BOUCLE EST OBLIGATOIRE ICI ---
    for index, row in rattrapages.iterrows():
        chapitre = row['Chapitre']
        matiere = row['Matiere']
        
        st.write(f"Matière: {matiere} | Chapitre: {chapitre}")
        
        # Le bouton est DANS la boucle, il connait donc 'chapitre' et 'matiere'
        if st.button(f"Réintégrer {chapitre} au planning", key=f"btn_{row['ID']}"):
            max_cours = st.session_state.config.get('max_cours_par_jour', 3)
            today = dt.date.today()
            date_limite = today + dt.timedelta(days=7)
            date_trouvee = None
            
            # Recherche de place
            for i in range(14):
                d = today + dt.timedelta(days=i)
                if d.weekday() == 6: continue
                
                count_day = len(st.session_state.data[
                    (pd.to_datetime(st.session_state.data['Date']).dt.date == d) & 
                    (st.session_state.data['Dossier'] == choix_dos)
                ])
                if count_day < max_cours:
                    date_trouvee = d
                    break
            
            if not date_trouvee:
                date_trouvee = today + dt.timedelta(days=(6 - today.weekday()))
            
            # Action de réintégration
            if date_trouvee and date_trouvee <= date_limite:
                new_rap = {'ID': str(uuid.uuid4()), 'Dossier': choix_dos, 'Matiere': matiere, 'Chapitre': chapitre, 'J_Type': 'RAP', 'Date': str(date_trouvee), 'Note': 0, 'Statut': 'À faire'}
                st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_rap])])
                # Nettoyage pour ne plus avoir le rattrapage dans le dashboard
                st.session_state.data = st.session_state.data[~((st.session_state.data['Chapitre'] == chapitre) & (st.session_state.data['Statut'] == 'À rattraper'))]
                save_data(st.session_state.data)
                st.success("Réintégré avec succès !")
                st.rerun()
            else:
                st.warning("Impossible : planning saturé ou date limite dépassée.")
# --- PLANNING & SAISIE ---
elif page == "Planning & Saisie":
    import uuid

    # --- 1. AJOUT SÉCURISÉ (Supprime uniquement les doublons exacts) ---
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
                            new_rows.append({
                                'ID': str(uuid.uuid4()), 'Dossier': choix_dos, 'Matiere': mat, 
                                'Chapitre': chap, 'J_Type': f'J{j}', 'Date': str(date_j), 
                                'Note': 0, 'Statut': 'À faire'
                            })
                    
                    # Concaténation
                    st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame(new_rows)])
                    
                    # NETTOYAGE SÉCURISÉ : On ne supprime que si TOUT est identique
                    st.session_state.data = st.session_state.data.drop_duplicates(
                        subset=['Dossier', 'Chapitre', 'J_Type', 'Date'], keep='first'
                    )
                    save_data(st.session_state.data)
                    st.rerun()

    # --- 2. PLANNING HEBDO (Affichage robuste) ---
    st.subheader("🗓️ Planning Hebdomadaire")
    cols = st.columns(7)
    jours = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
    today = dt.date.today()
    start_week = today - dt.timedelta(days=today.weekday())
    
    for i, col in enumerate(cols):
        day = start_week + dt.timedelta(days=i)
        with col:
            st.markdown(f"**{jours[i]}**\n{day.strftime('%d/%m')}")
            # Conversion sécurisée des dates
            temp_df = st.session_state.data.copy()
            temp_df['Date_Obj'] = pd.to_datetime(temp_df['Date']).dt.date
            
            df_day = temp_df[(temp_df['Date_Obj'] == day) & (temp_df['Dossier'] == choix_dos)]
            for _, r in df_day.iterrows():
                st.caption(f"{r['Chapitre']} ({r['J_Type']})")

    # --- 3. SAISIE NOTES (Affichage robuste) ---
    st.divider()
    st.subheader(f"Saisie Notes - Aujourd'hui")
    
    # Même logique de conversion pour être sûr de trouver les données
    temp_df = st.session_state.data.copy()
    temp_df['Date_Obj'] = pd.to_datetime(temp_df['Date']).dt.date
    df_today = temp_df[(temp_df['Date_Obj'] == today) & (temp_df['Dossier'] == choix_dos)].copy()

    if not df_today.empty:
        edited = st.data_editor(
            df_today[['ID', 'Chapitre', 'J_Type', 'Statut', 'Note']],
            column_config={"ID": None}, hide_index=True, use_container_width=True
        )
        if st.button("💾 Enregistrer"):
            # Mise à jour des notes et statuts ligne par ligne
            for _, row in edited.iterrows():
                # On cherche l'ID exact dans le dataframe principal
                mask = st.session_state.data['ID'] == row['ID']
                st.session_state.data.loc[mask, 'Note'] = row['Note']
                st.session_state.data.loc[mask, 'Statut'] = row['Statut']
            
            # Sauvegarde physique
            save_data(st.session_state.data)
            
            # Message de confirmation
            st.success("Notes enregistrées avec succès !")
            
            # --- REDIRECTION FORCÉE ---
            # On change la valeur de la page pour rebasculer sur le Dashboard
            st.session_state.page = "Dashboard" 
            st.rerun()
    else:
        st.info("Aucun chapitre prévu aujourd'hui.")


# --- GRAPHIQUES ---
elif page == "Graphiques":
    st.title("📊 Progression")
    for mat in st.session_state.config['dossiers'].get(choix_dos, []):
        st.subheader(f"📚 {mat}")
        st.table(st.session_state.data[(st.session_state.data['Matiere'] == mat) & (st.session_state.data['Note'] > 0)][['Date', 'Note']].tail(3))