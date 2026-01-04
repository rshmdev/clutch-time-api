# NBA Betting Analytics API

API FastAPI para análises e acompanhamento de jogos da NBA em tempo real.

## Funcionalidades

- 📊 Listagem de jogos por data
- 🔴 Detalhes de jogos ao vivo
- 📈 Play-by-play em tempo real
- 🔌 WebSocket para atualizações em tempo real

## Instalação

1. Clone o repositório:
```bash
git clone <url-do-repositorio>
cd betnba
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Executando a API

```bash
uvicorn app:app --reload
```

A API estará disponível em `http://127.0.0.1:8000`

## Documentação Interativa

Acesse `http://127.0.0.1:8000/docs` para a documentação interativa do Swagger.

## Endpoints Principais

- `GET /games/{date}` - Lista jogos de uma data específica (formato: YYYY-MM-DD)
- `GET /games/{game_id}/details` - Detalhes completos de um jogo
- `GET /games/{game_id}/playbyplay` - Play-by-play de um jogo
- `WS /ws/games/{game_id}` - WebSocket para atualizações em tempo real

## Tecnologias

- FastAPI
- nba_api
- pandas
- uvicorn

## Licença

MIT

