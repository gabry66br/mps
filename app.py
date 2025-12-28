import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from scipy.stats import poisson
import time

# ==========================================
# INSERISCI LA TUA CHIAVE API TRA LE VIRGOLETTE
# ==========================================
API_KEY = "ec63324b70c4ac4077192f858866098b" 
# ==========================================

st.set_page_config(page_title="AI Calcio Live PRO", layout="wide")

def get_live_matches():
    url = "https://v3.football.api-sports.io/fixtures?live=all"
    headers = {'x-apisports-key': API_KEY, 'x-rapidapi-host': "v3.football.api-sports.io"}
    try:
        res = requests.get(url, headers=headers).json()
        return res.get('response', [])
    except:
        return []

def get_stats(fixture_id):
    url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fixture_id}"
    headers = {'x-apisports-key': API_KEY, 'x-rapidapi-host': "v3.football.api-sports.io"}
    try:
        res = requests.get(url, headers=headers).json()
        return res.get('response', [])
    except:
        return []

def calcola_prob(stats, minuto):
    # Estraiamo i dati tecnici
    s_data = {s['type']: s['value'] for s in stats[0]['statistics'] if s['value'] is not None}
    attacchi_p = int(s_data.get('Dangerous Attacks', 0))
    tiri = int(s_data.get('Shots on Goal', 0))
    # Calcolo pressione
    pressione = (attacchi_p * 0.4) + (tiri * 4)
    lambda_gol = (pressione / 100) * (1 + (minuto / 90)) * 0.3
    prob = (1 - poisson.pmf(0, lambda_gol)) * 100
    return round(min(prob, 98), 1)

st.title("⚽ AI Calcio Live PRO")
st.subheader("Analisi in tempo reale delle partite in corso")

partite = get_live_matches()

if not partite:
    st.info("Nessuna partita live in questo momento. L'app si aggiornerà appena iniziano i match!")
else:
    for p in partite[:8]: # Analizza le prime 8 partite più importanti
        f_id = p['fixture']['id']
        casa = p['teams']['home']['name']
        ospite = p['teams']['away']['name']
        score = f"{p['goals']['home']} - {p['goals']['away']}"
        minuto = p['fixture']['status']['elapsed']
        campionato = p['league']['name']

        # Recupera statistiche per questa partita
        statistiche = get_stats(f_id)
        
        col1, col2 = st.columns([1, 2])
        with col1:
            st.write(f"**{campionato}**")
            st.markdown(f"### {casa} vs {ospite}")
            st.metric("Punteggio", score, f"{minuto}'")
        
        with col2:
            if statistiche:
                pressione_score = calcola_prob(statistiche, minuto)
                st.write(f"**Probabilità Gol nei prossimi 10 minuti:**")
                st.progress(pressione_score / 100)
                
                if pressione_score > 70:
                    st.error(f"🔥 ALTA PRESSIONE: {pressione_score}% - Possibile Gol!")
                elif pressione_score > 40:
                    st.warning(f"⚡ In pressione: {pressione_score}%")
                else:
                    st.success(f"📉 Fase calma: {pressione_score}%")
            else:
                st.write("In attesa di dati statistici dal campo...")
        
        st.divider()

st.caption("Aggiornamento automatico ogni 90 secondi. Non chiudere la pagina per monitorare.")
time.sleep(90)
st.rerun()
