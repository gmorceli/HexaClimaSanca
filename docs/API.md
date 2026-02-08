# API HexaCloud - Referência

## Autenticação

A API usa OAuth2 via AWS Cognito.

- **Token URL:** `https://auth.hexacloud.com.br/oauth2/token`
- **Client ID:** `bmqgtcosbo6i3irv3ojkfjjoj`
- **Redirect URI:** `http://localhost:3000`
- **API Base:** `https://m73akbtcad.execute-api.us-east-2.amazonaws.com/v1/`

### Fluxo de autenticação

1. Obter `authorization_code` via login no navegador
2. Trocar o code por tokens (`access_token`, `refresh_token`)
3. Usar `access_token` no header `Authorization: Bearer <token>`
4. Tokens expiram em 1h; usar `refresh_token` para renovar

## Endpoints

### Devices

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/devices` | Listar dispositivos |
| GET | `/devices/{device_id}` | Detalhes de um dispositivo |
| POST | `/devices` | Registrar dispositivo |
| DELETE | `/devices/{device_id}` | Remover dispositivo |

**Parâmetros de query (GET /devices):**
- `user_id` - Filtrar por usuário
- `device_id` - Filtrar por dispositivo
- `session` - Filtrar por sessão
- `lat`, `lon`, `radius_km` - Filtro geográfico

### Users

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/users` | Listar usuários |
| GET | `/users/{user_id}` | Detalhes de um usuário |
| POST | `/users` | Criar usuário |
| PATCH | `/users/{user_id}` | Atualizar usuário |
| DELETE | `/users/{user_id}` | Remover usuário |

### Query (Dados Climáticos)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/query` | Consultar dados climáticos |

**Parâmetros de query:**
- `start_ts` - Timestamp início (epoch)
- `end_ts` - Timestamp fim (epoch)
- `user_id` - Filtrar por usuário
- `session` - Filtrar por sessão
- `device_id` - Filtrar por dispositivo
- `lat`, `lon`, `radius_km` - Filtro geográfico

## Exemplo de device.json

```json
{
  "device_id": "11:22:33:44",
  "lat": -21.9,
  "lon": -47.9,
  "session": "test-session"
}
```

## Exemplo de user.json

```json
{
  "user_id": "c1cbd550-b051-7041-c5e1-346915a0192f",
  "status": "active",
  "plan": "premium",
  "quota_requests_minute": 60,
  "quota_requests_day": 1000,
  "quota_mb_month": 500,
  "role": "user"
}
```
