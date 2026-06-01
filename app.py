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
        try:
            df = pd.read_csv(DATA_FILE)
            # Conversion stricte : on force le format jour en premier
            df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce').dt.date
            df['Note'] = pd.to_numeric(df['Note'], errors='coerce').fillna(0)
            return df
        except: return pd.DataFrame(columns=cols)
    return pd.DataFrame(columns=cols)

def save_data(df): df.to_csv(DATA_FILE, index=False)

# ... (Configuration reste identique)

# --- PAGES ---
# Dans DASHBOARD (Rattrapages) :
    st.subheader("⚠️ Rattrapages")
    if not df.empty:
        # On force la conversion en numérique pour éviter le bug
        df['Note'] = pd.to_numeric(df['Note'], errors='coerce')
        rattrapages = df[(df['Note'] > 0) & (df['Note'] < 12)]
        if not rattrapages.empty:
            # Formatage de la date pour l'affichage en français
            disp_df = rattrapages.copy()
            disp_df['Date'] = disp_df['Date'].apply(lambda x: x.strftime('%d/%m/%Y'))
            st.table(disp_df[['Matiere', 'Chapitre', 'J_Type', 'Date', 'Note']])

# Dans PLANNING (Génération) :
    # Utilise st.date_input qui gère nativement le format localisé du navigateur
    d0 = st.date_input("Date J0", value=dt.date.today())
    ex = st.date_input("Date Examen", value=None)

# Dans GRAPHIQUES :
    if not df.empty:
        df_clean = df[pd.to_numeric(df['Note'], errors='coerce') > 0].copy()
        if not df_clean.empty:
            # On force la date en string formatée pour éviter les erreurs de tri Pandas
            df_clean['Date_Str'] = df_clean['Date'].apply(lambda x: x.strftime('%d/%m/%Y'))
            pivot_df = df_clean.pivot_table(index='Date_Str', columns='Matiere', values='Note', aggfunc='mean')
            st.line_chart(pivot_df)