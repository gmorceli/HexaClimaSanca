# HexaClimaSanca

Análise de dados climáticos de São Carlos/SP usando a API HexaCloud.

## Configuração

1. Instale as dependências:
```bash
pip install -r requirements.txt
```

2. Autentique-se na API (veja `docs/API.md` para detalhes):
```bash
python api/auth.py --code SEU_AUTHORIZATION_CODE
```

3. Execute a coleta de dados:
```bash
python api/query.py --days 30
```

## Estrutura do Projeto

```
HexaClimaSanca/
├── api/              # Módulos de acesso à API HexaCloud
│   ├── auth.py       # Autenticação OAuth2 (Cognito)
│   └── query.py      # Consulta de dados climáticos
├── docs/             # Documentação
│   └── API.md        # Referência da API HexaCloud
├── data/             # Dados coletados (não versionado)
└── analysis/         # Scripts de análise
```
