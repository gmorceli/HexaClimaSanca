# HexaClimaSanca

Mapa interativo de chuva acumulada em Sao Carlos/SP usando dados das estacoes meteorologicas da rede HexaCloud.

## Mapa ao Vivo

O mapa esta disponivel online via Railway (link apos deploy).

## Funcionalidades

- Coleta de dados de 31 estacoes meteorologicas via API HexaCloud
- Tratamento de outliers em 2 estagios:
  1. Leituras individuais acima de 2x o maximo da referencia sao zeradas
  2. Estacoes com acumulado > 4x a referencia sao marcadas como suspeitas
- Estacao de referencia: Defesa Civil SC (defesacivilsc01)
- Mapa interativo com Folium (heatmap + marcadores coloridos)
- Legenda: verde (baixa), laranja (moderada), vermelho (alta), azul (referencia), cinza (suspeita)

## Configuracao Local

1. Instale as dependencias:
```bash
pip install -r requirements.txt
```

2. Autentique-se na API (veja `docs/API.md`):
```bash
python api/auth.py --code SEU_AUTHORIZATION_CODE
```

3. Gere o mapa:
```bash
python analysis/mapa_chuva_24h.py --data-file data/raw_24h.json
```

4. Servidor local:
```bash
python server.py
```

## Estrutura do Projeto

```
HexaClimaSanca/
  api/              # Modulos de acesso a API HexaCloud
    auth.py         # Autenticacao OAuth2 (Cognito)
    query.py        # Consulta de dados climaticos
  analysis/         # Scripts de analise
    mapa_chuva_24h.py  # Gera mapa de calor da chuva 24h
  docs/             # Documentacao
    API.md          # Referencia da API HexaCloud
  output/           # Mapas gerados (HTML)
  data/             # Dados coletados (nao versionado)
  server.py         # Servidor web para Railway
  Procfile          # Config Railway
```

## Deploy no Railway

O projeto usa um servidor HTTP simples (`server.py`) que serve os arquivos da pasta `output/`. O Railway detecta automaticamente o `Procfile`.
