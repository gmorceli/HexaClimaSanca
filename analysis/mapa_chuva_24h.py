#!/usr/bin/env python3
"""
Mapa de calor da chuva acumulada nas últimas 24h em São Carlos/SP.
Usa dados da API HexaCloud com tratamento de outliers.
"""

import sys, os, json, time
import requests
import pandas as pd
import numpy as np
import folium
from folium.plugins import HeatMap

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))
from auth import get_access_token, API_BASE

# Estações de São Carlos (do sessions_cache)
STATIONS = [
    {"session": "cdcc", "device_id": "E8:07:BD:2A:DA:03", "lat": -22.01914, "lon": -47.89281},
    {"session": "defesacivilsc01", "device_id": "83:CC:2C:26:60:4A", "lat": -22.03028, "lon": -47.88289},
    {"session": "julianoneto", "device_id": "24:1C:9F:19:91:5E", "lat": -22.01658, "lon": -47.87471},
    {"session": "padariagenebra", "device_id": "D5:40:CB:B0:8A:92", "lat": -21.99390, "lon": -47.89734},
    {"session": "id1-i2c-400", "device_id": "6C:7B:A8:1D:81:23", "lat": -21.99377, "lon": -47.89967},
    {"session": "central", "device_id": "23:3E:C5:BD:A5:FA", "lat": -22.02472, "lon": -47.88990},
    {"session": "aracedesantoantonio", "device_id": "33:D5:90:5A:AD:F3", "lat": -21.93067, "lon": -47.93563},
    {"session": "interpav-backup", "device_id": "E0:3F:97:2F:47:4E", "lat": -21.96485, "lon": -47.92235},
    {"session": "soufadoalexandre", "device_id": "08:EF:22:B0:8A:86", "lat": -21.92943, "lon": -47.87267},
    {"session": "cruzeirodosul", "device_id": "C3:E9:2E:0C:66:55", "lat": -22.04922, "lon": -47.89262},
    {"session": "estadio-luisao", "device_id": "C3:14:CB:C1:7C:56", "lat": -22.03059, "lon": -47.90162},
    {"session": "id1-emeja-sc", "device_id": "4A:F0:A3:25:E8:FC", "lat": -22.01587, "lon": -47.89327},
    {"session": "alvaroguiao", "device_id": "89:6D:FF:4A:A9:51", "lat": -22.01366, "lon": -47.89011},
    {"session": "conegomanoeltobias", "device_id": "0B:E6:EC:D0:CE:71", "lat": -22.01516, "lon": -47.88099},
    {"session": "douradinho", "device_id": "C6:EE:F7:C8:ED:FC", "lat": -22.01823, "lon": -47.84974},
    {"session": "id1-eldorado", "device_id": "C3:2C:CF:87:16:83", "lat": -21.98069, "lon": -47.92736},
    {"session": "jardim-beatriz", "device_id": "7D:0F:9A:31:49:C9", "lat": -22.03499, "lon": -47.90786},
    {"session": "espraiado", "device_id": "D1:17:71:61:03:83", "lat": -21.98914, "lon": -47.87558},
    {"session": "stevenson02", "device_id": "82:CF:9A:99:05:7F", "lat": -22.02464, "lon": -47.88940},
    {"session": "recreiosaojudas", "device_id": "EC:7B:BC:56:4A:CA", "lat": -22.03483, "lon": -47.86581},
    {"session": "atheneu", "device_id": "15:7F:22:57:B7:35", "lat": -22.00565, "lon": -47.91950},
    {"session": "kartodromo", "device_id": "EE:11:CF:60:B6:24", "lat": -21.99690, "lon": -47.89948},
    {"session": "synnus", "device_id": "4F:74:C3:78:83:C5", "lat": -22.00079, "lon": -47.90330},
    {"session": "interpav01", "device_id": "58:73:5A:ED:65:F5", "lat": -21.96487, "lon": -47.92259},
    {"session": "babilonia", "device_id": "9E:6F:67:58:DA:8F", "lat": -22.02711, "lon": -47.78021},
    {"session": "centenario", "device_id": "21:A0:1D:A9:EE:00", "lat": -21.99934, "lon": -47.90682},
    {"session": "parqtec", "device_id": "19:04:7D:89:A9:D7", "lat": -22.00751, "lon": -47.88130},
    {"session": "tendtudo02", "device_id": "7D:FC:BB:4F:EF:FE", "lat": -22.02464, "lon": -47.88940},
    {"session": "trabalhocomfraternidade", "device_id": "1D:CC:75:85:9A:BB", "lat": -22.02241, "lon": -47.91130},
    {"session": "aracy01", "device_id": "9D:D7:75:9E:F4:71", "lat": -22.05587, "lon": -47.90264},
    {"session": "stevenson01", "device_id": "3B:4A:C0:A5:6F:B4", "lat": -22.02464, "lon": -47.88940},
    {"session": "ct-nicolas-santos", "device_id": "AB:17:FC:E0:0C:A1", "lat": -22.03713, "lon": -47.83046},
    {"session": "janete-lia", "device_id": "29:B0:58:38:9E:FC", "lat": -22.04112, "lon": -47.89530},
]

STATION_MAP = {s["device_id"]: s for s in STATIONS}
REFERENCE_SESSION = "defesacivilsc01"
REFERENCE_DEVICE = "83:CC:2C:26:60:4A"
QUERY_URL = API_BASE.rstrip("/") + "/query"

# Sessões excluídas manualmente (dados não confiáveis)
EXCLUDED_SESSIONS = {"interpav-backup", "conegomanoeltobias"}

# São Carlos centro
SC_LAT = -22.01
SC_LON = -47.89
RADIUS_KM = 20


def treat_outlier_readings(df):
    """
    Remove leituras individuais outliers de cada estação, mantendo a estação no resultado.

    Estratégia:
    1. Usa a estação de referência (defesacivilsc01) para determinar o threshold
       máximo razoável por leitura individual.
    2. Leituras acima desse threshold são descartadas (sensor bugado).
    3. Estações com poucas leituras (< 10% da referência) são removidas.
    4. Sessões na lista EXCLUDED_SESSIONS são removidas.
    """
    print("\n=== TRATAMENTO DE OUTLIERS (por leitura individual) ===")

    # 1. Excluir sessões manuais
    session_map_inv = {s["device_id"]: s["session"] for s in STATIONS}
    df["session"] = df["device_id"].map(session_map_inv)
    excluded = df[df["session"].isin(EXCLUDED_SESSIONS)]
    if len(excluded) > 0:
        excluded_sessions = excluded["session"].unique()
        print(f"Sessoes excluidas manualmente: {list(excluded_sessions)}")
    df = df[~df["session"].isin(EXCLUDED_SESSIONS)].copy()

    # 2. Calcular threshold a partir da referência
    ref = df[df["device_id"] == REFERENCE_DEVICE]
    ref_rain = ref["rain"]
    ref_nonzero = ref_rain[ref_rain > 0]
    ref_count = len(ref)

    if len(ref_nonzero) > 0:
        ref_max = ref_rain.max()
        # Threshold: 2x o máximo da referência
        threshold = ref_max * 2
        print(f"Referencia ({REFERENCE_SESSION}): max/leitura={ref_max:.2f}mm, {ref_count} leituras")
        print(f"Threshold por leitura: {threshold:.2f}mm (2x max da referencia)")
    else:
        # Fallback: usar percentil global
        all_nonzero = df["rain"][df["rain"] > 0]
        threshold = all_nonzero.quantile(0.99) * 2 if len(all_nonzero) > 0 else 10
        print(f"Referencia sem dados de chuva. Threshold fallback: {threshold:.2f}mm")

    # 3. Contar e remover leituras outliers por estação
    total_before = len(df)
    outlier_mask = df["rain"] > threshold
    n_outliers = outlier_mask.sum()

    if n_outliers > 0:
        outlier_by_session = df[outlier_mask].groupby("session")["rain"].agg(["count", "sum", "max"])
        print(f"\nLeituras outliers removidas (>{threshold:.2f}mm):")
        for session, row in outlier_by_session.iterrows():
            print(f"  {session}: {int(row['count'])} leituras removidas (max={row['max']:.1f}mm, soma_removida={row['sum']:.1f}mm)")

    # Zerar leituras outliers (ao invés de remover a linha, zeramos o rain)
    df.loc[outlier_mask, "rain"] = 0.0

    print(f"\nTotal: {n_outliers} leituras zeradas de {total_before}")
    return df, ref_count, threshold


def compute_accumulated_rain(df, ref_count):
    """Calcula chuva acumulada por estação após tratamento de outliers."""

    # Acumular chuva por device_id
    rain_by_device = df.groupby("device_id")["rain"].sum().reset_index()
    rain_by_device.columns = ["device_id", "rain_acc"]

    # Contagem de leituras por device
    counts = df.groupby("device_id")["rain"].count().reset_index()
    counts.columns = ["device_id", "n_readings"]
    rain_by_device = rain_by_device.merge(counts, on="device_id")

    # Adicionar lat/lon e session das estações
    rain_by_device["lat"] = rain_by_device["device_id"].map(lambda d: STATION_MAP.get(d, {}).get("lat"))
    rain_by_device["lon"] = rain_by_device["device_id"].map(lambda d: STATION_MAP.get(d, {}).get("lon"))
    rain_by_device["session"] = rain_by_device["device_id"].map(lambda d: STATION_MAP.get(d, {}).get("session", "desconhecida"))

    # Remover devices sem coordenadas conhecidas
    rain_by_device = rain_by_device.dropna(subset=["lat", "lon"])

    # Remover estações com poucas leituras (< 10% da referência)
    min_readings = max(int(ref_count * 0.10), 1)
    low = rain_by_device[rain_by_device["n_readings"] < min_readings]
    if len(low) > 0:
        print(f"Removidas por poucas leituras (<{min_readings}): {list(low['session'])}")
    rain_by_device = rain_by_device[rain_by_device["n_readings"] >= min_readings].copy()

    # Remover chuva negativa
    rain_by_device = rain_by_device[rain_by_device["rain_acc"] >= 0].copy()

    # Marcar estações suspeitas (acumulado > 4x a referência) mas manter no mapa
    ref_row = rain_by_device[rain_by_device["session"] == REFERENCE_SESSION]
    rain_by_device["suspect"] = False
    if not ref_row.empty:
        ref_acc = ref_row["rain_acc"].values[0]
        if ref_acc > 0:
            suspect_mask = (
                (rain_by_device["rain_acc"] > ref_acc * 4)
                & (rain_by_device["session"] != REFERENCE_SESSION)
            )
            rain_by_device.loc[suspect_mask, "suspect"] = True
            suspect = rain_by_device[suspect_mask]
            if len(suspect) > 0:
                print(f"Marcadas como suspeitas (>4x {ref_acc:.1f}mm) - mantidas no mapa:")
                for _, r in suspect.iterrows():
                    print(f"  {r['session']}: {r['rain_acc']:.1f}mm")

    print(f"Estacoes finais: {len(rain_by_device)}")
    return rain_by_device


def build_heatmap(df, output_file):
    """Gera mapa de calor interativo com Folium."""
    center_lat = df["lat"].mean()
    center_lon = df["lon"].mean()

    m = folium.Map(location=[center_lat, center_lon], zoom_start=13, tiles="OpenStreetMap")

    # Dados para o heatmap: [lat, lon, intensidade]
    max_rain = df["rain_acc"].max()
    if max_rain == 0:
        max_rain = 1  # evitar divisão por zero

    heat_data = []
    for _, row in df.iterrows():
        heat_data.append([row["lat"], row["lon"], row["rain_acc"]])

    # Adicionar HeatMap
    HeatMap(
        heat_data,
        radius=30,
        blur=25,
        max_zoom=15,
        min_opacity=0.4,
        gradient={0.2: "blue", 0.4: "cyan", 0.6: "lime", 0.8: "yellow", 1.0: "red"},
    ).add_to(m)

    # Separar estações confiáveis e suspeitas para o heatmap
    reliable = df[~df.get("suspect", False)]

    # Adicionar marcadores com info de cada estação
    for _, row in df.iterrows():
        is_suspect = row.get("suspect", False)

        if is_suspect:
            color = "gray"
        elif row["session"] == REFERENCE_SESSION:
            color = "darkblue"
        elif row["rain_acc"] < reliable["rain_acc"].median():
            color = "green"
        elif row["rain_acc"] > reliable["rain_acc"].quantile(0.75):
            color = "red"
        else:
            color = "orange"

        status = " (DADOS SUSPEITOS - sensor com calibracao irregular)" if is_suspect else ""
        popup_text = (
            f"<b>{row['session']}</b>{status}<br>"
            f"Chuva acum.: <b>{row['rain_acc']:.1f} mm</b><br>"
            f"Leituras: {row['n_readings']}<br>"
            f"Device: {row['device_id']}"
        )

        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=8 + (row["rain_acc"] / max_rain) * 12,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7 if not is_suspect else 0.4,
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=f"{row['session']}: {row['rain_acc']:.1f}mm{'  [SUSPEITO]' if is_suspect else ''}",
        ).add_to(m)

    # Legenda
    legend_html = """
    <div style="position:fixed; bottom:50px; left:50px; z-index:1000;
                background-color:white; padding:10px; border:2px solid grey;
                border-radius:5px; font-size:13px;">
        <b>Chuva Acumulada 24h</b><br>
        <i style="background:green;width:12px;height:12px;display:inline-block;border-radius:50%;"></i> Baixa<br>
        <i style="background:orange;width:12px;height:12px;display:inline-block;border-radius:50%;"></i> Moderada<br>
        <i style="background:red;width:12px;height:12px;display:inline-block;border-radius:50%;"></i> Alta<br>
        <hr>
        <i style="background:darkblue;width:12px;height:12px;display:inline-block;border-radius:50%;"></i> Referencia (Defesa Civil)<br>
        <i style="background:gray;width:12px;height:12px;display:inline-block;border-radius:50%;"></i> Dados suspeitos (sensor)
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    m.save(output_file)
    print(f"\nMapa salvo em: {output_file}")
    return m


def print_summary(df):
    """Imprime resumo estatístico."""
    print("\n=== RESUMO DA CHUVA EM SÃO CARLOS (24h) ===")
    print(f"Estações analisadas: {len(df)}")
    print(f"Chuva média: {df['rain_acc'].mean():.1f} mm")
    print(f"Chuva mediana: {df['rain_acc'].median():.1f} mm")
    print(f"Máxima: {df['rain_acc'].max():.1f} mm ({df.loc[df['rain_acc'].idxmax(), 'session']})")
    print(f"Mínima: {df['rain_acc'].min():.1f} mm ({df.loc[df['rain_acc'].idxmin(), 'session']})")
    print()

    # Ranking
    ranked = df.sort_values("rain_acc", ascending=False)
    print("Ranking de chuva acumulada:")
    for i, (_, row) in enumerate(ranked.iterrows(), 1):
        marker = " [REF]" if row["session"] == REFERENCE_SESSION else ""
        print(f"  {i:2d}. {row['session']:<30s} {row['rain_acc']:6.1f} mm  ({row['n_readings']} leituras){marker}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Mapa de calor - Chuva 24h São Carlos")
    parser.add_argument("--code", help="Authorization code (se precisar renovar token)")
    parser.add_argument("--output", default=None, help="Arquivo HTML de saída")
    parser.add_argument("--data-file", help="Usar dados de arquivo JSON ao invés da API")
    args = parser.parse_args()

    output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    os.makedirs(output_dir, exist_ok=True)
    output_file = args.output or os.path.join(output_dir, "mapa_chuva_24h.html")

    if args.data_file:
        with open(args.data_file) as f:
            records = json.load(f)
        print(f"Carregados {len(records)} registros de {args.data_file}")
    else:
        print("Erro: use --data-file para carregar dados coletados.")
        sys.exit(1)

    # Criar DataFrame
    df = pd.DataFrame(records)
    df["time"] = pd.to_datetime(df["time"])
    df["rain"] = pd.to_numeric(df["rain"], errors="coerce").fillna(0)

    # Tratamento de outliers por leitura individual
    df, ref_count, threshold = treat_outlier_readings(df)

    # Acumular chuva por estação
    df = compute_accumulated_rain(df, ref_count)

    print("\n--- Apos tratamento ---")
    print(df[["session", "rain_acc", "n_readings"]].sort_values("rain_acc", ascending=False).to_string(index=False))

    print_summary(df)
    build_heatmap(df, output_file)

    # Salvar dados tratados
    data_file = os.path.join(output_dir, "chuva_24h_tratada.json")
    df.to_json(data_file, orient="records", indent=2, force_ascii=False)
    print(f"Dados tratados salvos em: {data_file}")


if __name__ == "__main__":
    main()
