import streamlit as st
import pandas as pd
import requests
from scipy.stats import poisson
import time

# ==========================================
# CONFIGURAZIONE
# ==========================================
API_KEY = "ec63324b70c4ac4077192f858866098b" 
st.set_page_config(page_title="Predittore Pro", layout="wide", initial_sidebar_state="collapsed")

# CSS personalizzato per renderlo simile a un'app mobile
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stMetric { background-color: white; padding: 10px; border-radius: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    .match-card { background-color: white; padding: 15px; border-radius: 15px; border-left: 5px solid #007bff; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .high-prob { border-left: 5px solid #ff4b4b !important; background-color: #fff5f5; }
    </style>
    """, unsafe_all__html=True)

def get_live_matches():
    url = "https://v3.football.api-sports.io/fixtures?live=all"
    headers = {'x-apisports-key': API_KEY, 'x-rapidapi-host': "v3.football.api-sports.io"}
    try:
        res = requests.get(url, headers=headers).json()
        return res.get('response', [])
    except: return []

def get_stats(fixture_id):
    url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fixture_id}"
    headers = {'x-apisports-key': API_KEY, 'x-rapidapi-host': "v3.football.api-sports.io"}
    try:
        res = requests.get(url, headers=headers).json()
        return res.get('response', [])
    except: return []

def calcola_prob(stats, minuto):
    try:
        s_home = {s['type']: s['value'] for s in stats[0]['statistics'] if s['value'] is not None}
        s_away = {s['type']: s['value'] for s in stats[1]['statistics'] if s['value'] is not None}
        
        # Sommiamo la pressione di entrambe le squadre
        attacchi_p = int(s_home.get('Dangerous Attacks', 0)) + int(s_away.get('Dangerous Attacks', 0))
        tiri = int(s_home.get('Shots on Goal', 0)) + int(s_away.get('Shots on Goal', 0))
        
        pressione = (attacchi_p * 0.45) + (tiri * 4.5)
        lambda_gol = (pressione / 100) * (1 + (minuto / 90)) * 0.28
        prob = (1 - poisson.pmf(0, lambda_gol)) * 100
        return round(min(prob, 99), 1), attacchi_p, tiri
    except: return 0, 0, 0

st.title("⚽ Live Goal Predictor")
st.write(f"Ultimo aggiornamento: {time.strftime('%H:%M:%S')}")

partite = get_live_matches()

if not partite:
    st.info("Nessuna partita live disponibile.")
else:
    for p in partite[:10]:
        f_id = p['fixture']['id']
        casa = p['teams']['home']['name']
        ospite = p['teams']['away']['name']
        score = f"{p['goals']['home']} - {p['goals']['away']}"
        minuto = p['fixture']['status']['elapsed']
        league = p['league']['name']
        logo_league = p['league']['logo']

        stats_res = get_stats(f_id)
        prob, att_p, tiri = calcola_prob(stats_res, minuto) if stats_res else (0,0,0)

        # Design della Card
        card_style = "match-card high-prob" if prob > 65 else "match-card"
        
        with st.container():
            st.markdown(f"""
                <div class="{card_style}">
                    <img src="{logo_league}" width="25"> <b>{league}</b><br>
                    <span style="font-size: 20px; font-weight: bold;">{casa} {score} {ospite}</span><br>
                    <span style="color: gray;">Minuto: {minuto}'</span>
                </div>
            """, unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Probabilità Gol", f"{prob}%")
            with c2:
                st.metric("Attacchi Peric.", att_p)
            with c3:
                st.metric("Tiri in Porta", tiri)
            
            if prob > 70:
                st.error("🚨 SEGNALE: Pressione altissima. Possibile gol a breve!")
            st.write("---")

# Refresh automatico più lento per risparmiare API (120 secondi)
time.sleep(120)
st.rerun()
