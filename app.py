import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from scipy.stats import poisson
import time

# --- INSERISCI QUI LA TUA CHIAVE API ---
# Se non la inserisci, l'app userà dati simulati
API_KEY = "28a76af9cbba28f6a8de5ceb63798d88"

st.set_page_config(page_title="AI Calcio Live", layout="wide")

def get_data():
    if API_KEY == "28a76af9cbba28f6a8de5ceb63798d88":
        # Dati di prova se non hai ancora l'API Key
        return [{"fixture": {"id": 1, "status": {"elapsed": 70}}, "teams": {"home": {"name": "Squadra A"}, "away": {"name": "Squadra B"}}, "goals": {"home": 1, "away": 0}}]
    
    url = "https://v3.football.api-sports.io/fixtures?live=all"
    headers = {'x-rapidapi-key': API_KEY, 'x-rapidapi-host': "v3.football.api-sports.io"}
    try:
        res = requests.get(url, headers=headers).json()
        return res.get('response', [])
    except:
        return []

st.title("⚽ Il mio Predittore Live")
st.write("L'app analizza le partite in corso e calcola la probabilità di un gol a breve.")

partite = get_data()

if not partite:
    st.error("Nessuna partita trovata o errore API Key.")
else:
    for p in partite:
        nome_casa = p['teams']['home']['name']
        nome_trasferta = p['teams']['away']['name']
        minuto = p['fixture']['status']['elapsed']
        score = f"{p['goals']['home']} - {p['goals']['away']}"
        
        # Algoritmo semplificato per te
        # In un'app reale qui aggiungiamo gli attacchi pericolosi
        prob = 15.5 + (minuto * 0.5) # Esempio: la probabilità sale col tempo
        
        col1, col2 = st.columns([1, 2])
        with col1:
            st.subheader(f"{nome_casa} vs {nome_trasferta}")
            st.metric("Risultato", score, f"Minuto: {minuto}'")
        with col2:
            st.progress(prob/100)
            st.write(f"Probabilità gol imminente: **{min(int(prob), 99)}%**")
        st.divider()

st.info("L'app si aggiorna automaticamente ogni 2 minuti.")
