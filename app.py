from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from nba_client import NBAClient
import pandas as pd
import numpy as np
import asyncio
import json

app = FastAPI(title="NBA Betting Analytics API", description="API para análises e previsões de jogos da NBA", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

client = NBAClient()

@app.websocket("/ws/games/{game_id}")
async def websocket_game_updates(websocket: WebSocket, game_id: str):
    await websocket.accept()
    try:
        while True:
            # Fetch live game details
            details = client.get_game_details(game_id)
            if details:
                print(f"Sending game update for game {game_id}")
                await websocket.send_json({"type": "game_update", "data": details})
            
            # Fetch play-by-play
            pbp = client.get_play_by_play(game_id)
            if pbp:
                print(f"Sending play-by-play update for game {game_id}")
                await websocket.send_json({"type": "playbyplay_update", "data": pbp})
            
            # Wait 30 seconds before next update
            await asyncio.sleep(10)
    except Exception as e:
        print(f"WebSocket error for game {game_id}: {e}")
    finally:
        await websocket.close()

@app.get("/")
def read_root():
    return {"message": "NBA Betting Analytics API", "version": "1.0.0"}

@app.get("/games/{date}")
def get_games_by_date(date: str):
    games = client.get_games_by_date(date)
    return {"games": games}

@app.get("/games/{game_id}/details")
def get_game_details(game_id: str):
    details = client.get_game_details(game_id)
    if not details:
        raise HTTPException(status_code=404, detail="Jogo não encontrado")
    return {"details": details}

@app.get("/games/{game_id}/playbyplay")
def get_play_by_play(game_id: str):
    pbp = client.get_play_by_play(game_id)
    return {"play_by_play": pbp}
