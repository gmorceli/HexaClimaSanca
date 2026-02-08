#!/usr/bin/env python3
"""Consulta dados climáticos da API HexaCloud."""

import argparse, requests, json, time, os, statistics
import concurrent.futures
from auth import get_access_token

API_URL = "https://m73akbtcad.execute-api.us-east-2.amazonaws.com/v1/query"


def fetch_range(start_ts, end_ts, headers, device_id=None, session=None, lat=None, lon=None, radius_km=None):
    params = {"start_ts": start_ts, "end_ts": end_ts}
    if device_id:
        params["device_id"] = device_id
    if session:
        params["session"] = session
    if lat and lon and radius_km:
        params["lat"] = lat
        params["lon"] = lon
        params["radius_km"] = radius_km

    t0 = time.time()
    resp = requests.get(API_URL, params=params, headers=headers)
    duration = time.time() - t0

    if resp.status_code == 200:
        data = resp.json()
        return {"duration": duration, "count": data.get("count", 0), "data": data.get("data", [])}
    else:
        print(f"[ERRO] {resp.status_code}: {resp.text}")
        return {"duration": duration, "count": 0, "data": []}


def main():
    parser = argparse.ArgumentParser(description="Consulta dados climáticos HexaCloud")
    parser.add_argument("--days", type=int, default=10, help="Número de dias para consultar")
    parser.add_argument("--device-id", help="Filtrar por device_id")
    parser.add_argument("--session", help="Filtrar por session")
    parser.add_argument("--lat", type=float, help="Latitude para filtro geográfico")
    parser.add_argument("--lon", type=float, help="Longitude para filtro geográfico")
    parser.add_argument("--radius-km", type=float, help="Raio em km")
    parser.add_argument("--code", help="Authorization code (se precisar renovar)")
    parser.add_argument("--output", default=None, help="Arquivo de saída (default: data/dados_Xdias.json)")
    args = parser.parse_args()

    token = get_access_token(args.code)
    headers = {"Authorization": f"Bearer {token}"}

    end_ts = int(time.time())
    start_ts = end_ts - (args.days * 24 * 3600)
    interval = 24 * 3600
    ranges = [(t, min(t + interval, end_ts)) for t in range(start_ts, end_ts, interval)]

    results, metrics = [], []
    t_start = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        futures = [
            executor.submit(fetch_range, s, e, headers, args.device_id, args.session, args.lat, args.lon, args.radius_km)
            for s, e in ranges
        ]
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            results.extend(res["data"])
            metrics.append(res)

    total_duration = time.time() - t_start

    # Salvar dados
    output_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(output_dir, exist_ok=True)
    output_file = args.output or os.path.join(output_dir, f"dados_{args.days}_dias.json")
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Métricas
    durations = [m["duration"] for m in metrics]
    counts = [m["count"] for m in metrics]
    print(f"\n==== MÉTRICAS ====")
    print(f"Total pontos: {len(results)}")
    print(f"Tempo total: {total_duration:.2f}s")
    if durations:
        print(f"Médio/req: {statistics.mean(durations):.2f}s")
        print(f"Mais rápida: {min(durations):.2f}s | Mais lenta: {max(durations):.2f}s")
    if counts:
        print(f"Média pontos/dia: {statistics.mean(counts):.1f}")
    print(f"Arquivo salvo em: {output_file}")


if __name__ == "__main__":
    main()
