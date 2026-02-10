#!/usr/bin/env python3
"""
Servidor web com atualizacao automatica do mapa de chuva a cada 20 minutos.
Coleta dados das ultimas 24h via API HexaCloud e regenera o mapa.
"""

import os
import sys
import json
import time
import threading
import requests
import concurrent.futures
from http.server import HTTPServer, SimpleHTTPRequestHandler
from datetime import datetime, timezone, timedelta

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
MAP_FILE = os.path.join(OUTPUT_DIR, "mapa_chuva_24h.html")

# Adicionar paths para imports
sys.path.insert(0, os.path.join(BASE_DIR, "api"))
sys.path.insert(0, os.path.join(BASE_DIR, "analysis"))

# Configuracao
PORT = int(os.environ.get("PORT", 8080))
UPDATE_INTERVAL = 20 * 60  # 20 minutos em segundos
USER_ID = "91ab0570-50b1-7099-1d86-2ad3631e780e"

# Auth via env vars (Railway) ou token_cache.json (local)
REFRESH_TOKEN = os.environ.get("HEXA_REFRESH_TOKEN", "")
TOKEN_URL = "https://us-east-2dq7vvrkkx.auth.us-east-2.amazoncognito.com/oauth2/token"
CLIENT_ID = "bmqgtcosbo6i3irv3ojkfjjoj"
API_BASE = "https://m73akbtcad.execute-api.us-east-2.amazonaws.com/v1/"
QUERY_URL = API_BASE.rstrip("/") + "/query"

# Cache de token em memoria
_token_cache = {"access_token": None, "expires_at": 0, "refresh_token": REFRESH_TOKEN}


def get_token():
    """Obtem access token, renovando se necessario."""
    global _token_cache

    # Se temos env var de refresh token, usar ela
    if not _token_cache["refresh_token"] and REFRESH_TOKEN:
        _token_cache["refresh_token"] = REFRESH_TOKEN

    # Se nao temos refresh token do env, tentar token_cache.json local
    if not _token_cache["refresh_token"]:
        cache_file = os.path.join(BASE_DIR, "token_cache.json")
        if os.path.exists(cache_file):
            with open(cache_file) as f:
                local_cache = json.load(f)
            _token_cache["refresh_token"] = local_cache.get("refresh_token", "")
            _token_cache["access_token"] = local_cache.get("access_token")
            _token_cache["expires_at"] = local_cache.get("expires_at", 0)

    # Token ainda valido?
    if _token_cache["access_token"] and time.time() < _token_cache["expires_at"] - 60:
        return _token_cache["access_token"]

    # Renovar via refresh token
    if _token_cache["refresh_token"]:
        print("Renovando access token...")
        data = {
            "grant_type": "refresh_token",
            "client_id": CLIENT_ID,
            "refresh_token": _token_cache["refresh_token"],
        }
        r = requests.post(TOKEN_URL, data=data,
                          headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=15)
        if r.status_code == 200:
            tokens = r.json()
            _token_cache["access_token"] = tokens["access_token"]
            _token_cache["expires_at"] = int(time.time()) + tokens.get("expires_in", 3600)
            print("Token renovado com sucesso")
            return _token_cache["access_token"]
        else:
            print(f"Erro ao renovar token: {r.status_code} {r.text}")

    print("AVISO: Sem token valido. Mapa nao sera atualizado.")
    return None


# Estacoes (mesma lista do mapa_chuva_24h.py)
STATIONS = [
    {"session": "cdcc", "device_id": "E8:07:BD:2A:DA:03"},
    {"session": "defesacivilsc01", "device_id": "83:CC:2C:26:60:4A"},
    {"session": "julianoneto", "device_id": "24:1C:9F:19:91:5E"},
    {"session": "padariagenebra", "device_id": "D5:40:CB:B0:8A:92"},
    {"session": "id1-i2c-400", "device_id": "6C:7B:A8:1D:81:23"},
    {"session": "central", "device_id": "23:3E:C5:BD:A5:FA"},
    {"session": "aracedesantoantonio", "device_id": "33:D5:90:5A:AD:F3"},
    {"session": "soufadoalexandre", "device_id": "08:EF:22:B0:8A:86"},
    {"session": "cruzeirodosul", "device_id": "C3:E9:2E:0C:66:55"},
    {"session": "estadio-luisao", "device_id": "C3:14:CB:C1:7C:56"},
    {"session": "id1-emeja-sc", "device_id": "4A:F0:A3:25:E8:FC"},
    {"session": "alvaroguiao", "device_id": "89:6D:FF:4A:A9:51"},
    {"session": "douradinho", "device_id": "C6:EE:F7:C8:ED:FC"},
    {"session": "id1-eldorado", "device_id": "C3:2C:CF:87:16:83"},
    {"session": "jardim-beatriz", "device_id": "7D:0F:9A:31:49:C9"},
    {"session": "espraiado", "device_id": "D1:17:71:61:03:83"},
    {"session": "stevenson02", "device_id": "82:CF:9A:99:05:7F"},
    {"session": "recreiosaojudas", "device_id": "EC:7B:BC:56:4A:CA"},
    {"session": "atheneu", "device_id": "15:7F:22:57:B7:35"},
    {"session": "kartodromo", "device_id": "EE:11:CF:60:B6:24"},
    {"session": "synnus", "device_id": "4F:74:C3:78:83:C5"},
    {"session": "interpav01", "device_id": "58:73:5A:ED:65:F5"},
    {"session": "babilonia", "device_id": "9E:6F:67:58:DA:8F"},
    {"session": "centenario", "device_id": "21:A0:1D:A9:EE:00"},
    {"session": "parqtec", "device_id": "19:04:7D:89:A9:D7"},
    {"session": "tendtudo02", "device_id": "7D:FC:BB:4F:EF:FE"},
    {"session": "trabalhocomfraternidade", "device_id": "1D:CC:75:85:9A:BB"},
    {"session": "aracy01", "device_id": "9D:D7:75:9E:F4:71"},
    {"session": "stevenson01", "device_id": "3B:4A:C0:A5:6F:B4"},
    {"session": "ct-nicolas-santos", "device_id": "AB:17:FC:E0:0C:A1"},
    {"session": "janete-lia", "device_id": "29:B0:58:38:9E:FC"},
]

EXCLUDED_SESSIONS = {"interpav-backup", "conegomanoeltobias"}


def fetch_session_day(session, start_ts, end_ts, headers):
    """Busca dados de uma sessao para um bloco de 24h."""
    params = {
        "session": session,
        "user_id": USER_ID,
        "start_ts": start_ts,
        "end_ts": end_ts,
    }
    try:
        resp = requests.get(QUERY_URL, params=params, headers=headers, timeout=30)
        if resp.status_code == 200:
            return resp.json().get("data", [])
        elif resp.status_code == 429 or "Limite" in resp.text:
            time.sleep(2)
            resp = requests.get(QUERY_URL, params=params, headers=headers, timeout=30)
            if resp.status_code == 200:
                return resp.json().get("data", [])
        else:
            print(f"  [ERRO] {session}: {resp.status_code}")
    except Exception as ex:
        print(f"  [EXCEPT] {session}: {ex}")
    return []


def collect_24h_data(token):
    """Coleta dados das ultimas 24h de todas as estacoes."""
    headers = {"Authorization": f"Bearer {token}"}
    end_ts = int(time.time())
    start_ts = end_ts - (24 * 3600)

    stations = [s for s in STATIONS if s["session"] not in EXCLUDED_SESSIONS]
    all_records = []

    print(f"Coletando dados de {len(stations)} estacoes...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(fetch_session_day, s["session"], start_ts, end_ts, headers): s["session"]
            for s in stations
        }
        for f in concurrent.futures.as_completed(futures):
            session = futures[f]
            data = f.result()
            all_records.extend(data)
            if data:
                print(f"  {session}: {len(data)} registros")

    print(f"Total coletado: {len(all_records)} registros")
    return all_records


def update_map():
    """Coleta dados e regenera o mapa."""
    br_tz = timezone(timedelta(hours=-3))
    now_br = datetime.now(br_tz).strftime("%d/%m/%Y %H:%M")
    print(f"\n{'='*50}")
    print(f"[{now_br}] Iniciando atualizacao do mapa...")

    token = get_token()
    if not token:
        print("Sem token - pulando atualizacao")
        return False

    try:
        records = collect_24h_data(token)
        if len(records) < 100:
            print(f"Poucos dados coletados ({len(records)}). Mantendo mapa anterior.")
            return False

        # Importar e gerar mapa
        from mapa_chuva_24h import generate_map
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        generate_map(records, MAP_FILE)

        print(f"Mapa atualizado com sucesso ({len(records)} registros)")
        return True

    except Exception as ex:
        print(f"Erro ao atualizar mapa: {ex}")
        import traceback
        traceback.print_exc()
        return False


def updater_loop():
    """Thread que atualiza o mapa a cada 20 minutos."""
    # Primeira atualizacao ao iniciar
    time.sleep(5)  # Esperar servidor subir
    update_map()

    while True:
        time.sleep(UPDATE_INTERVAL)
        update_map()


class MapHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=OUTPUT_DIR, **kwargs)

    def do_GET(self):
        if self.path == "/" or self.path == "":
            self.path = "/mapa_chuva_24h.html"
        return super().do_GET()

    def log_message(self, format, *args):
        # Reduzir log verboso
        pass


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Se nao existe mapa ainda, criar um placeholder
    if not os.path.exists(MAP_FILE):
        with open(MAP_FILE, "w", encoding="utf-8") as f:
            f.write("<html><body><h1>Mapa em atualizacao...</h1>"
                    "<p>O mapa sera gerado em alguns instantes. Recarregue a pagina.</p>"
                    "</body></html>")

    # Iniciar thread de atualizacao
    updater = threading.Thread(target=updater_loop, daemon=True)
    updater.start()
    print(f"Thread de atualizacao iniciada (intervalo: {UPDATE_INTERVAL//60} min)")

    # Iniciar servidor HTTP
    server = HTTPServer(("0.0.0.0", PORT), MapHandler)
    print(f"Servidor rodando em http://0.0.0.0:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
