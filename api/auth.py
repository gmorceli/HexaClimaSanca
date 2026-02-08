#!/usr/bin/env python3
"""Módulo de autenticação OAuth2 para a API HexaCloud via AWS Cognito."""

import argparse, requests, sys, json, time, os

TOKEN_URL = "https://auth.hexacloud.com.br/oauth2/token"
CLIENT_ID = "bmqgtcosbo6i3irv3ojkfjjoj"
API_BASE = "https://m73akbtcad.execute-api.us-east-2.amazonaws.com/v1/"
REDIRECT_URI = "http://localhost:3000"
CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "token_cache.json")


def save_cache(tokens):
    tokens["expires_at"] = int(time.time()) + tokens.get("expires_in", 3600)
    with open(CACHE_FILE, "w") as f:
        json.dump(tokens, f)


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            return json.load(f)
    return {}


def exchange_code_for_tokens(code, token_url=TOKEN_URL, client_id=CLIENT_ID):
    data = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }
    r = requests.post(token_url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    if r.status_code == 400 and "invalid_grant" in r.text:
        raise RuntimeError("Esse authorization code já foi usado ou expirou. Gere um novo código no login.")
    r.raise_for_status()
    tokens = r.json()
    save_cache(tokens)
    return tokens


def refresh_tokens(refresh_token, token_url=TOKEN_URL, client_id=CLIENT_ID):
    data = {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "refresh_token": refresh_token,
    }
    r = requests.post(token_url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    r.raise_for_status()
    tokens = r.json()
    tokens["refresh_token"] = refresh_token
    save_cache(tokens)
    return tokens


def get_access_token(code=None):
    cache = load_cache()
    if code:
        return exchange_code_for_tokens(code)["access_token"]
    if cache:
        if time.time() < cache.get("expires_at", 0):
            return cache["access_token"]
        elif "refresh_token" in cache:
            return refresh_tokens(cache["refresh_token"])["access_token"]
    print("Nenhum token válido. Rode com --code primeiro.")
    sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Autenticação HexaCloud API")
    parser.add_argument("--code", help="Authorization code do login")
    args = parser.parse_args()
    token = get_access_token(args.code)
    print(f"Token obtido com sucesso (expira em 1h)")
