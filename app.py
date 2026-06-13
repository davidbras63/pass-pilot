import streamlit as st
import pandas as pd
import datetime as dt
import uuid
import requests
import json
import time
import altair as alt
import streamlit.components.v1 as components

st.set_page_config(layout="wide")

WEB_APP_URL = "https://script.google.com/macros/s/AKfycbwA7ZGCqHcDgw_Ia2PDjuvLqGDx1smoqR75VOo5IytV-QgMIw2_6xnZtXI1sFensDDwfw/exec"

def load_data_from_sheet():
    try:
        response = requests.get(WEB_APP_URL, timeout=15)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data.get('data', []), columns=['Dossier', 'Matiere', 'Chapitre', 'J_Type', 'Date', 'Note', 'Statut', 'ID'])
            df['Date'] = df['Date'].astype(str).apply(lambda x: x[:10])
            config = data.get('config')
            if config is None:
                st.error("Configuration absente.")
                st.stop()
            return df, config
    except Exception as e:
        st.error(f"Erreur : {e}")
        st.stop()
    st.error("Erreur de connexion.")
    st.stop()

def save_all_to_sheet(df, config):
    # --- VERROU DE SÉCURITÉ ---
    # 1. Empêche l'exécution automatique pendant les 3 premières secondes du démarrage
    if 'start_time' not in st.session_state:
        st.session_state.start_time = time.time()
    if time.time() - st.session_state.start_time < 3:
        return
   
    # 2. Si le tableau est vide, on refuse de sauvegarder pour protéger Google Sheets
    if df is None or df.empty:
        return

    # --- SAUVEGARDE ---
    df_to_send = df.copy()
    df_to_send['Date'] = df_to_send['Date'].astype(str)
    df_to_send['Note'] = df_to_send['Note'].astype(str)
    payload = {"data": df_to_send.values.tolist(), "config": config}
    try:
        requests.post(WEB_APP_URL, json=payload, timeout=15)
        time.sleep(0.5)
    except:
        st.error("Erreur de sauvegarde")

# --- BLINDAGE FERMETURE ---
sync_script = f"""
    <script>
        window.addEventListener('beforeunload', function (e) {{
            const data_payload = {json.dumps(st.session_state.data.values.tolist() if 'data' in st.session_state else [])};
            const config_payload = {json.dumps(st.session_state.config if 'config' in st.session_state else {})};
            navigator.sendBeacon('{WEB_APP_URL}', JSON.stringify({{"data": data_payload, "config": config_payload}}));
        }});
    </script>
"""
components.html(sync_script, height=0)

if 'data' not in st.session_state:
    st.session_state.data, st.session_state.config = load_data_from_sheet()

   
    # 2. Notification visuelle
    st.sidebar.success("Données enregistrées !")
    
    # 3. Rafraîchissement forcé pour mettre à jour les moyennes partout
    st.rerun()

def reset_dossier():
    nom = st.session_state.d_in
    if nom and nom not in st.session_state.config['dossiers']:
        st.session_state.config['dossiers'][nom] = []
    st.session_state.d_in = ""

def reset_matiere():
    nom = st.session_state.m_in
    if nom and nom not in st.session_state.config['dossiers'][choix_dos]:
        st.session_state.config['dossiers'][choix_dos].append(nom)
    st.session_state.m_in = ""

st.sidebar.title("⚙️ Pilot Expert")

# BOUTON PRIORITAIRE : Il est en haut de tout, impossible à manquer
if st.sidebar.button("💾 SAUVEGARDER TOUT"):
    save_all_to_sheet(st.session_state.data, st.session_state.config)
    st.sidebar.success("Enregistré !")

# Ensuite, tes réglages en dessous
with st.sidebar.expander("🛠️ Réglages", expanded=False):
    st.session_state.config['cours_max'] = st.number_input("Max cours/jour", 1, 20, int(st.session_state.config.get('cours_max', 5)))
    cad_str = st.text_input("Cadencier (jours)", ",".join(map(str, st.session_state.config['cadencier'])))
    st.session_state.config['cadencier'] = [int(x.strip()) for x in cad_str.split(",")]
    
    for j in st.session_state.config['cadencier']:
        st.session_state.config['seuils'][str(j)] = st.slider(f"Seuil Note J{j}", 10, 20, int(st.session_state.config['seuils'].get(str(j), 12)))

choix_dos = st.sidebar.selectbox("Dossier", list(st.session_state.config['dossiers'].keys()))
st.sidebar.text_input("Nouveau Dossier", key="d_in")
st.sidebar.button("➕ Créer Dossier", on_click=reset_dossier)
st.sidebar.text_input("Nom Matière", key="m_in")
st.sidebar.button("➕ Ajouter Matière", on_click=reset_matiere)
# Initialisation de l'état de la page si inexistant
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

# Création du menu radio qui utilise la valeur mémorisée
page = st.sidebar.radio(
    "Navigation", 
    ["Dashboard", "Planning & Saisie", "Graphiques"], 
    index=["Dashboard", "Planning & Saisie", "Graphiques"].index(st.session_state.page)
)
st.sidebar.markdown("---") # Ligne de séparation
st.sidebar.subheader("🔗 Raccourcis")

# --- 1. BOUTON BIOMÉDAL ---
if 'url_biomedal' not in st.session_state.config:
    st.session_state.config['url_biomedal'] = ""

url_bio = st.session_state.config['url_biomedal']

if url_bio:
    st.sidebar.link_button("🏥 Biomédal", url_bio, use_container_width=True)
else:
    with st.sidebar.popover("⚙️ Configurer Biomédal", use_container_width=True):
        lien_bio = st.text_input("Colle le lien Biomédal ici :", key="input_bio")
        if st.button("Enregistrer Biomédal", key="btn_bio"):
            st.session_state.config['url_biomedal'] = lien_bio
            st.rerun()

# --- 2. BOUTON FAC ---
if 'url_fac' not in st.session_state.config:
    st.session_state.config['url_fac'] = ""

url_fac = st.session_state.config['url_fac']

if url_fac:
    st.sidebar.link_button("🎓 Fac", url_fac, use_container_width=True)
else:
    with st.sidebar.popover("⚙️ Configurer la Fac", use_container_width=True):
        lien_fac = st.text_input("Colle le lien de la Fac ici :", key="input_fac")
        if st.button("Enregistrer la Fac", key="btn_fac"):
            st.session_state.config['url_fac'] = lien_fac
            st.rerun()

# Mise à jour de la valeur mémorisée après chaque clic
st.session_state.page = page

if page == "Dashboard":
    st.title(f"🎯 Dashboard : {choix_dos}")
    with st.popover("🚨 Supprimer le dossier ?"):
        st.error("⚠️ ATTENTION : Tu vas supprimer TOUT le dossier de suivi. Cette action est irréversible !")
        if st.button("Confirmer la suppression du dossier"):
            # ... METS ICI ton code de suppression (décalé vers la droite avec TAB) ...
            del st.session_state.config['dossiers'][choix_dos]
            st.session_state.data = st.session_state.data[st.session_state.data['Dossier'] != choix_dos]
            st.rerun()
   
    for m in st.session_state.config['dossiers'].get(choix_dos, []):
        with st.expander(f"📚 {m}"):
            c1, c2 = st.columns([4, 1])
            with c2.popover("🗑️ Supprimer", key=f"pop_{m}"):
                st.error(f"🚨 Confirmer la suppression de {m} ?")
                if st.button("Oui, supprimer définitivement", key=f"del_{m}"):
                    st.session_state.config['dossiers'][choix_dos].remove(m)
                    st.session_state.data = st.session_state.data[(st.session_state.data['Dossier'] != choix_dos) | (st.session_state.data['Matiere'] != m)]
                    st.rerun()
            chapitres_matiere = st.session_state.data[(st.session_state.data['Dossier'] == choix_dos) & (st.session_state.data['Matiere'] == m)]['Chapitre'].unique()
            if len(chapitres_matiere) > 0:
                st.write("**Chapitres :**")
                for c in chapitres_matiere:
                    col_ch, col_pb = st.columns([0.8, 0.2])
                    col_ch.write(f"- {c}")
                    with col_pb.popover("🗑️", key=f"pop_chap_{choix_dos}_{m}_{c}"):
                        st.error(f"Supprimer le chapitre {c} ?")
                        if st.button("Confirmer", key=f"del_chap_{choix_dos}_{m}_{c}"):
                            st.session_state.data = st.session_state.data[
                                ~((st.session_state.data['Dossier'] == choix_dos) & 
                                (st.session_state.data['Matiere'] == m) & 
                                (st.session_state.data['Chapitre'] == c))
                            ]
                            st.success(f"Chapitre '{c}' supprimé !")
                            st.rerun()
           
    st.subheader("⚠️ Rattrapages à traiter")
    df_dos = st.session_state.data[st.session_state.data['Dossier'] == choix_dos].copy()
    def est_en_rattrapage(row):
        try: note = float(str(row['Note']).replace(',', '.'))
        except: note = 0
        j_str = str(row['J_Type']).replace('J', '').replace('R', '')
        seuil = int(st.session_state.config['seuils'].get(j_str, 12))
        return note > 0 and note < seuil and row['Statut'] != 'Traité'
    rattrapages = df_dos[df_dos.apply(est_en_rattrapage, axis=1)]
    if not rattrapages.empty:
        for _, row in rattrapages.iterrows():
            c1, c2, c3 = st.columns([0.6, 0.2, 0.2])
            c1.write(f"{row['Matiere']} | {row['Chapitre']} ({row['J_Type']}) | Note: {row['Note']}")
            if c2.button("Réintégrer", key=f"btn_{row['ID']}"):
                date_debut = dt.datetime.strptime(row['Date'], '%Y-%m-%d')
                all_dates = sorted(st.session_state.data[(st.session_state.data['Chapitre'] == row['Chapitre']) & (st.session_state.data['Dossier'] == choix_dos)]['Date'].unique())
                next_date_str = all_dates[all_dates.index(row['Date']) + 1] if (all_dates.index(row['Date']) + 1) < len(all_dates) else (date_debut + dt.timedelta(days=365)).strftime('%Y-%m-%d')
                date_limite = dt.datetime.strptime(next_date_str, '%Y-%m-%d')
                place_trouvee = False
                for delta in range(1, 60):
                    test_date = (date_debut + dt.timedelta(days=delta)).strftime('%Y-%m-%d')
                    if dt.datetime.strptime(test_date, '%Y-%m-%d') >= date_limite: break
                    if test_date not in st.session_state.data[(st.session_state.data['Chapitre'] == row['Chapitre']) & (st.session_state.data['Dossier'] == choix_dos)]['Date'].values:
                        new_row = row.copy()
                        new_row['ID'], new_row['J_Type'], new_row['Date'] = str(uuid.uuid4()), f"{row['J_Type'].replace('R','')}R", test_date
                        new_row['Note'], new_row['Statut'] = 0, 'À faire'
                        st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=True)
                        st.session_state.data.loc[st.session_state.data['ID'] == row['ID'], 'Statut'] = 'Traité'
                        place_trouvee = True; break
                if place_trouvee: st.rerun()
                else: st.error("❌ Aucune place disponible pour réintégrer.")
            if c3.button("🗑️ Supprimer", key=f"trash_{row['ID']}"):
                st.session_state.data.loc[st.session_state.data['ID'] == row['ID'], 'Statut'] = 'Traité'
                st.rerun()

elif page == "Planning & Saisie":
    with st.expander("✍️ Ajouter Chapitre", expanded=True):
        with st.form("Add_Form", clear_on_submit=True):
            mat = st.selectbox("Matière", st.session_state.config['dossiers'].get(choix_dos, []))
            chap = st.text_input("Titre")
            d0_date = st.date_input("Date J0", value=dt.date.today())
            dex_date = st.date_input("Date Examen", value=None)
            submitted = st.form_submit_button("Générer Planning")
        if submitted and chap and dex_date:
            # On crée le J0
            new_rows = [{'ID': str(uuid.uuid4()), 'Dossier': choix_dos, 'Matiere': mat, 'Chapitre': chap, 'J_Type': 'J0', 'Date': str(d0_date), 'Note': 0, 'Statut': 'À faire'}]
            
            # On boucle sur la config DYNAMIQUE (ce que tu as dans la sidebar)
            for j in st.session_state.config['cadencier']:
                d_j = d0_date + dt.timedelta(days=j)
                if d_j <= dex_date:
                    new_rows.append({
                        'ID': str(uuid.uuid4()), 
                        'Dossier': choix_dos, 
                        'Matiere': mat, 
                        'Chapitre': chap, 
                        'J_Type': f'J{j}', 
                        'Date': str(d_j), 
                        'Note': 0, 
                        'Statut': 'À faire'
                    })
            
            # Mise à jour des données et sauvegarde
            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame(new_rows)]).drop_duplicates(subset=['Dossier', 'Chapitre', 'J_Type', 'Date'])
            save_all_to_sheet(st.session_state.data, st.session_state.config)
            st.rerun()

    st.subheader("🗓️ Planning Hebdomadaire")
    cols = st.columns(7)
    if 'semaine_decalage' not in st.session_state:
        st.session_state.semaine_decalage = 0

    col_g, col_c, col_d = st.columns([1, 1.5, 1])
    if col_g.button("⬅️", key="prev_week"):
        st.session_state.semaine_decalage -= 7
        st.rerun()
    if col_c.button("Aujourd'hui", key="today_week"):
        st.session_state.semaine_decalage = 0
        st.rerun()
    if col_d.button("➡️", key="next_week"):
        st.session_state.semaine_decalage += 7
        st.rerun()

    today = dt.date.today()
    start = today - dt.timedelta(days=today.weekday()) + dt.timedelta(days=st.session_state.semaine_decalage)

    for i, col in enumerate(cols):
        day_str = (start + dt.timedelta(days=i)).strftime('%Y-%m-%d')
        with col:
            st.markdown(f"**{day_str[8:]}/{day_str[5:7]}**")
            temp = st.session_state.data[(st.session_state.data['Date'] == day_str) & (st.session_state.data['Dossier'] == choix_dos)]
            for _, r in temp.iterrows():
                c1, c2 = st.columns([0.7, 0.3])
                with c1:
                    if st.checkbox(f"{r['Chapitre']} ({r['J_Type']})", value=(r['Statut'] == 'Fait'), key=f"chk_{r['ID']}"):
                        st.session_state.data.loc[st.session_state.data['ID'] == r['ID'], 'Statut'] = 'Fait'
                        #save_all_to_sheet(st.session_state.data, st.session_state.config)
                with c2:
                    if r['J_Type'] != 'J0':
                        new_date = st.date_input("", value=dt.datetime.strptime(r['Date'], '%Y-%m-%d'), key=f"cal_{r['ID']}", label_visibility="collapsed")
                        if str(new_date) != r['Date']:
                            st.session_state.data.loc[st.session_state.data['ID'] == r['ID'], 'Date'] = str(new_date)
                            #save_all_to_sheet(st.session_state.data, st.session_state.config)
                            st.rerun()
   
    # --- GRILLE DE SAISIE INTERACTIVE (VERSION STABLE) ---
    st.write("---")
    st.subheader("📝 Grille de Saisie des Notes")

    # 1. Copie locale pour sécuriser l'affichage
    df_saisie = st.session_state.data.copy()
    
    # Sécurité absolue : on s'assure que les 4 colonnes demandées existent dans le tableau
    if 'Chapitre_Complet' not in df_saisie.columns:
        df_saisie['Chapitre_Complet'] = 'Sans nom'
    else:
        df_saisie['Chapitre_Complet'] = df_saisie['Chapitre_Complet'].fillna('Sans nom').astype(str)

    if 'Type' not in df_saisie.columns:
        df_saisie['Type'] = 'J0'
    else:
        df_saisie['Type'] = df_saisie['Type'].fillna('J0').astype(str)

    if 'Statut' not in df_saisie.columns:
        df_saisie['Statut'] = 'À faire'
    else:
        df_saisie['Statut'] = df_saisie['Statut'].fillna('À faire').astype(str)

    if 'Note' not in df_saisie.columns:
        df_saisie['Note'] = ''
    df_saisie['Note'] = df_saisie['Note'].fillna('').astype(str)

    # 2. Configuration de l'éditeur (Ordre : Chapitre, Échéance, Statut, Note)
    config_colonnes = {
        "Chapitre_Complet": st.column_config.TextColumn("📚 Chapitre", disabled=True), 
        "Type": st.column_config.TextColumn("⏳ Échéance (J)", disabled=True),
        "Statut": st.column_config.SelectboxColumn("🔄 Statut", options=["À faire", "Fait"], required=True),
        "Note": st.column_config.TextColumn("✍️ Saisie Notes (Ex: 12 14.5 11)", help="Tapez vos notes séparées par un espace, puis TAB.")
    }

    # 3. Affichage de la grille interactive
    edited_df = st.data_editor(
        df_saisie[['Chapitre_Complet', 'Type', 'Statut', 'Note']],
        column_config=config_colonnes,
        use_container_width=True,
        hide_index=True,
        key="grille_saisie_clavier_fluide"
    )

    # 4. Bouton unique d'enregistrement et de calcul sous le tableau
    st.write("")
    if st.button("💾 Enregistrer et Calculer les Moyennes", use_container_width=True, type="primary"):
        if edited_df is not None:
            try:
                for idx_edit, row in edited_df.iterrows():
                    real_idx = df_saisie.index[idx_edit]
                    
                    # Sauvegarde des choix de l'utilisateur dans la vraie base
                    st.session_state.data.at[real_idx, 'Statut'] = row['Statut']
                    
                    # Extraction et calcul de la moyenne de la chaîne de notes
                    chaine_notes = str(row['Note']).strip()
                    if chaine_notes and chaine_notes != "nan":
                        # Si l'utilisateur a entré plusieurs chiffres séparés par des espaces
                        if not chaine_notes.replace('.', '', 1).isdigit():
                            try:
                                liste_chiffres = [float(x) for x in chaine_notes.split() if x.replace('.', '', 1).isdigit()]
                                if liste_chiffres:
                                    st.session_state.data.at[real_idx, 'Note'] = round(sum(liste_chiffres) / len(liste_chiffres), 1)
                            except:
                                pass
                        # Si c'est une note unique déjà calculée ou modifiée en direct
                        elif chaine_notes.replace('.', '', 1).isdigit():
                            st.session_state.data.at[real_idx, 'Note'] = float(chaine_notes)
                
                # Sauvegarde vers Google Sheets
                save_all_to_sheet(st.session_state.data, st.session_state.config)
                st.success("Toutes les données et moyennes ont été enregistrées avec succès ! 🎉")
                st.rerun()
            except Exception as e:
                st.error(f"Erreur lors de la sauvegarde : {e}")



elif page == "Graphiques":
    st.title("📊 Analyse Graphique de tes Notes")
    
    if "data" in st.session_state and not st.session_state.data.empty:
        df_graphes = st.session_state.data[st.session_state.data['Dossier'] == choix_dos].copy()
        
        # Détection automatique de la colonne Matière
        liste_matieres = sorted(df_graphes['Matière'].unique()) if 'Matière' in df_graphes.columns else []
        if not liste_matieres and 'Matiere' in df_graphes.columns:
            liste_matieres = sorted(df_graphes['Matiere'].unique())
            
        if liste_matieres:
            # Menu déroulant pour verrouiller une seule matière
            sel_mat_graph = st.selectbox("📚 Choisis la matière à analyser :", options=liste_matieres)
            
            # Filtrage étanche sur la matière choisie
            col_mat = 'Matière' if 'Matière' in df_graphes.columns else 'Matiere'
            df_mat_graph = df_graphes[df_graphes[col_mat] == sel_mat_graph].copy()
            
            # Nettoyage local des notes (virgules en points)
            df_mat_graph['Note_Num'] = pd.to_numeric(df_mat_graph['Note'].astype(str).str.replace(',', '.'), errors='coerce')
            df_mat_graph = df_mat_graph.dropna(subset=['Note_Num'])
            
            if not df_mat_graph.empty:
                # --- 1. GRAPHIQUE MOYENNE GÉNÉRALE DE LA MATIÈRE ---
                st.subheader(f"📈 Évolution de la moyenne ({sel_mat_graph})")
                df_mat_graph['Sort_Val'] = df_mat_graph['J_Type'].astype(str).str.extract('(\d+)').fillna(0).astype(float)
                df_mat_graph.loc[df_mat_graph['J_Type'].astype(str).str.contains('R', case=False, na=False), 'Sort_Val'] += 0.5
                
                df_moy_regroupee = df_mat_graph.groupby(['J_Type', 'Sort_Val'])['Note_Num'].mean().reset_index()
                df_moy_regroupee = df_moy_regroupee.sort_values('Sort_Val')
                
                chart_moyenne = alt.Chart(df_moy_regroupee).mark_line(point=True, color='blue').encode(
                    x=alt.X('J_Type', sort=alt.EncodingSortField(field='Sort_Val', order='ascending'), title='Échéance'),
                    y=alt.Y('Note_Num', scale=alt.Scale(domain=[0, 20]), title='Note Moyenne')
                ).properties(height=220)
                st.altair_chart(chart_moyenne, use_container_width=True)
                
                st.write("---")
                
                # --- 2. GRAPHES CÔTE À CÔTE FILTRÉS SUR LES THÈMES DE CETTE MATIÈRE ---
                st.subheader("📋 Comparaison individuelle des grands thèmes")
                df_mat_graph['Theme'] = df_mat_graph['Chapitre'].astype(str).str.replace(r'^\d+[\s-]*', '', regex=True).str.strip()
                liste_themes = sorted(df_mat_graph['Theme'].unique())
                
                themes_selectionnes = st.multiselect(
                    f"Sélectionne jusqu'à 3 thèmes de {sel_mat_graph} :", 
                    options=liste_themes, 
                    default=[liste_themes[0]] if liste_themes else None, 
                    max_selections=3
                )
                
                if themes_selectionnes:
                    cols = st.columns(len(themes_selectionnes))
                    for i, nom_theme in enumerate(themes_selectionnes):
                        with cols[i]:
                            st.markdown(f"**Thème : {nom_theme}**")
                            df_un_theme = df_mat_graph[df_mat_graph['Theme'] == nom_theme].copy()
                            if not df_un_theme.empty:
                                df_theme_regroupe = df_un_theme.groupby(['J_Type', 'Sort_Val'])['Note_Num'].mean().reset_index()
                                df_theme_regroupe = df_theme_regroupe.sort_values('Sort_Val')
                                chart_chapitre = alt.Chart(df_theme_regroupe).mark_line(point=True, color='orange').encode(
                                    x=alt.X('J_Type', sort=alt.EncodingSortField(field='Sort_Val', order='ascending'), title='Échéance'),
                                    y=alt.Y('Note_Num', scale=alt.Scale(domain=[0, 20]), title='Note Moyenne')
                                ).properties(height=180, title="Progression globale")
                                st.altair_chart(chart_chapitre, use_container_width=True)
                            else:
                                st.caption("Aucune note.")
                else:
                    st.info("Sélectionne au moins un thème.")
            else:
                st.info(f"Aucune note numérique valide pour {sel_mat_graph}.")
        else:
            st.info("Aucune matière trouvée dans le fichier.")
    else:
        st.info("Pas de données disponibles.")