import streamlit as st
import requests
from scipy.stats import poisson
import time

# ==========================================
# CONFIGURAZIONE
# ==========================================
API_KEY = "28a76af9cbba28f6a8de5ceb63798d88" 

# Lista ID aggiornata per il 2025 (Top Leagues)
TOP_LEAGUES = [135, 39, 140, 78, 61, 2, 3, 848, 253, 71, 128, 88, 94, 144]

st.set_page_config(page_title="AI Goal Predictor", layout="wide")

# CSS Migliorato
st.markdown("""
    <style>
    .match-card {
        background: #1e2130;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 15px;
        border: 1px solid #30363d;
        color: white;
    }
    .score-box {
        font-size: 22px; font-weight: bold; color: #00ff00;
        background: black; padding: 5px 15px; border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

def fetch_api(url):
    headers = {'x-apisports-key': API_KEY, 'x-rapidapi-host': "v3.football.api-sports.io"}
    try:
        response = requests.get(url, headers=headers)
        res_json = response.json()
        if res_json.get('errors'):
            st.error(f"Errore API: {res_json['errors']}")
            return []
        return res_json.get('response', [])
    except Exception as e:
        st.error(f"Errore connessione: {e}")
        return []

def calcola_prob(stats, minuto):
    try:
        s_h = {s['type']: s['value'] for s in stats[0]['statistics'] if s['value'] is not None}
        s_a = {s['type']: s['value'] for s in stats[1]['statistics'] if s['value'] is not None}
        att = int(s_h.get('Dangerous Attacks', 0)) + int(s_a.get('Dangerous Attacks', 0))
        tiri = int(s_h.get('Shots on Goal', 0)) + int(s_a.get('Shots on Goal', 0))
        pressione = (att * 0.45) + (tiri * 4.5)
        lambda_gol = (pressione / 100) * (1 + (minuto / 90)) * 0.35
        return round(min((1 - poisson.pmf(0, lambda_gol)) * 100, 99), 1), att, tiri
    except: return 0, 0, 0

st.title("⚽ AI Goal Predictor Live")

# Recupero partite live
all_matches = fetch_api("https://v3.football.api-sports.io/fixtures?live=all")

# Filtriamo per i top campionati
partite_top = [m for m in all_matches if m['league']['id'] in TOP_LEAGUES]

# Se non ci sono partite top, mostriamo le altre per test
if not all_matches:
    st.info("Nessuna partita live rilevata dall'API in questo momento. Potrebbe essere un momento di pausa tra i match.")
else:
    # Se la ricerca filtrata è vuota, usiamo tutte le partite per farti vedere che funziona
    visualizzate = partite_top if partite_top else all_matches[:10]
    
    if not partite_top:
        st.warning("⚠️ Nessun match nei 'Top Campionati' al momento. Mostro altri match live per test:")

    for p in visualizzate:
        f_id = p['fixture']['id']
        casa = p['teams']['home']
        ospite = p['teams']['away']
        score = f"{p['goals']['home']} - {p['goals']['away']}"
        minuto = p['fixture']['status']['elapsed']
        lega = p['league']

        # Mostriamo la card
        st.markdown(f"""
            <div class="match-card">
                <div style="font-size: 12px; color: #8b949e;">{lega['name']} (ID: {lega['id']})</div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top:10px;">
                    <div style="width: 35%; text-align: right;">{casa['name']} <img src="{casa['logo']}" width="30"></div>
                    <div class="score-box">{score}</div>
                    <div style="width: 35%; text-align: left;"><img src="{ospite['logo']}" width="30"> {ospite['name']}</div>
                </div>
                <div style="text-align: center; margin-top: 5px; font-size: 14px;">Minuto: {minuto}'</div>
            </div>
        """, unsafe_allow_html=True)

        # Statistiche e probabilità (solo se cliccate o caricate)
        stats = fetch_api(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={f_id}")
        if stats:
            prob, att, tiri = calcola_prob(stats, minuto)
            c1, c2, c3 = st.columns(3)
            c1.metric("Probabilità Gol", f"{prob}%")
            c2.metric("Attacchi Peric.", att)
            c3.metric("Tiri Porta", tiri)
            if prob > 75: st.error("🔥 SEGNALE GOL IMMINENTE")
        
        st.divider()

# DEBUG: Vediamo cosa sta succedendo "sotto il cofano"
with st.expander("🛠️ Debug Sistema (Clicca qui se non vedi partite)"):
    st.write(f"Partite totali trovate dall'API: {len(all_matches)}")
    st.write(f"Partite filtrate (Top Leagues): {len(partite_top)}")
    if all_matches:
        st.write("Esempio ID Lega trovati ora:", [m['league']['id'] for m in all_matches[:5]])

time.sleep(120)
st.rerun()
