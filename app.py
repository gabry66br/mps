import streamlit as st
import pandas as pd
import requests
from scipy.stats import poisson
import time

# ==========================================
# CONFIGURAZIONE E FILTRI
# ==========================================
API_KEY = "ec63324b70c4ac4077192f858866098b" 

# ID dei Campionati Top (API-Football IDs)
TOP_LEAGUES = [
    135, 39, 140, 78, 61,    # Serie A, Premier, La Liga, Bundesliga, Ligue 1
    2, 3, 848,               # Champions, Europa League, Conference
    253, 71, 128,            # MLS, Brasile, Argentina
    88, 94, 144              # Olanda, Portogallo, Belgio
]

st.set_page_config(page_title="Predittore Top Live", layout="wide")

# CSS per il design moderno
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .match-container {
        background: #1e2130;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 25px;
        border: 1px solid #30363d;
    }
    .team-box { text-align: center; font-weight: bold; font-size: 18px; }
    .score-box { 
        text-align: center; 
        font-size: 24px; 
        font-weight: 900; 
        color: #00ff00;
        background: #000;
        border-radius: 8px;
        padding: 5px;
    }
    .prob-bar-container { margin-top: 15px; }
    </style>
    """, unsafe_allow_html=True)

def get_live_data():
    url = "https://v3.football.api-sports.io/fixtures?live=all"
    headers = {'x-apisports-key': API_KEY, 'x-rapidapi-host': "v3.football.api-sports.io"}
    try:
        res = requests.get(url, headers=headers).json()
        all_matches = res.get('response', [])
        # Filtriamo solo i campionati che ci interessano
        return [m for m in all_matches if m['league']['id'] in TOP_LEAGUES]
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
        att_p = int(s_home.get('Dangerous Attacks', 0)) + int(s_away.get('Dangerous Attacks', 0))
        tiri = int(s_home.get('Shots on Goal', 0)) + int(s_away.get('Shots on Goal', 0))
        pressione = (att_p * 0.45) + (tiri * 4.5)
        lambda_gol = (pressione / 100) * (1 + (minuto / 90)) * 0.32
        prob = (1 - poisson.pmf(0, lambda_gol)) * 100
        return round(min(prob, 99), 1), att_p, tiri
    except: return 0, 0, 0

st.title("🏆 AI Goal Predictor: Top Leagues")
st.write(f"Aggiornamento live: {time.strftime('%H:%M:%S')}")

partite = get_live_data()

if not partite:
    st.info("Nessuna partita dei Top Campionati in corso. Torna durante i match di Serie A, Premier o MLS!")
else:
    for p in partite:
        f_id = p['fixture']['id']
        # Dati Casa
        c_nome = p['teams']['home']['name']
        c_logo = p['teams']['home']['logo']
        # Dati Ospite
        o_nome = p['teams']['away']['name']
        o_logo = p['teams']['away']['logo']
        
        score = f"{p['goals']['home']} - {p['goals']['away']}"
        minuto = p['fixture']['status']['elapsed']
        lega_nome = p['league']['name']

        # Recupero statistiche
        stats_res = get_stats(f_id)
        prob, att_p, tiri = calcola_prob(stats_res, minuto) if stats_res else (0,0,0)

        # UI MATCH CARD
        st.markdown(f"""
            <div class="match-container">
                <div style="text-align: center; color: #8b949e; margin-bottom: 10px;">{lega_nome}</div>
                <div style="display: flex; justify-content: space-around; align-items: center;">
                    <div class="team-box">
                        <img src="{c_logo}" width="50"><br>{c_nome}
                    </div>
                    <div>
                        <div class="score-box">{score}</div>
                        <div style="text-align: center; font-size: 14px; margin-top: 5px;">{minuto}'</div>
                    </div>
                    <div class="team-box">
                        <img src="{o_logo}" width="50"><br>{o_nome}
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Indicatori Sotto la Card
        c1, c2, c3 = st.columns(3)
        with c1:
            color = "red" if prob > 70 else "orange" if prob > 40 else "green"
            st.markdown(f"**Probabilità Gol:** <span style='color:{color}; font-size:20px;'>{prob}%</span>", unsafe_allow_html=True)
        with c2:
            st.write(f"🔥 Attacchi Peric: **{att_p}**")
        with c3:
            st.write(f"🎯 Tiri Porta: **{tiri}**")
        
        if prob > 70:
            st.error(f"🚨 SEGNALE GOL: {c_nome} vs {o_nome} è caldissima!")
        
        st.divider()

# Refresh ogni 3 minuti per preservare le chiamate API
time.sleep(180)
st.rerun()
