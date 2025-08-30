from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any

from . import database
from .services import sleeper_service
from .models.sleeper import User, League, Roster, Draft, Player, Stats, Transaction, Matchup, PlayerStint


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.create_tables()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/user/{username}", response_model=User)
async def get_user(username: str):
    user_data = await sleeper_service.client.get_user_by_username(username)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user_data)


@app.get("/user/{username}/leagues/{season}", response_model=List[League])
async def get_leagues_for_user(username: str, season: str):
    user_data = await sleeper_service.client.get_user_by_username(username)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    user_id = user_data["user_id"]
    leagues_data = await sleeper_service.client.get_leagues_for_user(user_id, season)
    return [League(**league) for league in leagues_data]


@app.get("/league/{league_id}/drafts", response_model=List[Draft])
async def get_league_drafts(league_id: str):
    drafts_data = await sleeper_service.client.get_league_drafts(league_id)
    return [Draft(**draft) for draft in drafts_data]


@app.get("/league/{league_id}/rosters", response_model=List[Roster])
async def get_league_rosters(league_id: str):
    rosters_data = await sleeper_service.client.get_league_rosters(league_id)
    return [Roster(**roster) for roster in rosters_data]


@app.get("/league/{league_id}/transactions/{week}", response_model=List[Transaction])
async def get_league_transactions(league_id: str, week: int):
    transactions_data = await sleeper_service.client.get_league_transactions(league_id, week)
    return [Transaction(**tx) for tx in transactions_data]


@app.get("/players", response_model=Dict[str, Player])
async def get_all_players():
    players_data = await sleeper_service.client.get_all_players()
    return {player_id: Player(**player_data) for player_id, player_data in players_data.items()}


@app.get("/league/{league_id}/history", response_model=List[League])
async def get_league_history(league_id: str):
    history_data = await sleeper_service.client.get_league_history(league_id)
    return [League(**league) for league in history_data]


@app.get("/league/{league_id}/transactions", response_model=List[Transaction])
async def get_all_league_transactions(league_id: str):
    return await sleeper_service.get_all_league_transactions(league_id)


@app.get("/league/{league_id}/player/{player_id}/lifecycle", response_model=List[Dict[str, Any]])
async def get_player_lifecycle(league_id: str, player_id: str):
    return await sleeper_service.get_player_lifecycle(league_id, player_id)


@app.get("/league/{league_id}/roster/{roster_id}/analysis", response_model=List[Dict[str, Any]])
async def get_roster_analysis(league_id: str, roster_id: int):
    return await sleeper_service.get_roster_analysis(league_id, roster_id)


@app.get("/stats/nfl/{season}", response_model=Dict[str, Dict[int, Stats]])
async def get_nfl_player_stats(season: str):
    return await sleeper_service.get_all_player_weekly_stats_for_season(season)


@app.get("/player/{player_id}/aggregated_stats/{season}", response_model=Dict[str, Any])
async def get_player_aggregated_stats(player_id: str, season: str):
    return await sleeper_service.get_player_aggregated_stats(player_id, season)


@app.get("/league/{league_id}/matchups/{week}", response_model=List[Matchup])
async def get_league_matchups(league_id: str, week: int):
    matchups_data = await sleeper_service.client.get_league_matchups(league_id, week)
    return [Matchup(**matchup) for matchup in matchups_data]


@app.get("/analysis/league/{league_id}/player/{player_id}/since_transaction/{transaction_id}", response_model=Dict[str, Any])
async def get_player_performance_since_transaction(league_id: str, player_id: str, transaction_id: str):
    return await sleeper_service.get_player_performance_since_transaction(league_id, player_id, transaction_id)


@app.get("/analysis/league/{league_id}/player/{player_id}/between_transactions/{transaction_id_x}/{transaction_id_y}", response_model=Dict[str, Any])
async def get_player_performance_between_transactions(league_id: str, player_id: str, transaction_id_x: str, transaction_id_y: str):
    return await sleeper_service.get_player_performance_between_transactions(league_id, player_id, transaction_id_x, transaction_id_y)


@app.get("/analysis/league/{league_id}/player/{player_id}/stints", response_model=List[PlayerStint])
async def get_player_stints(league_id: str, player_id: str):
    return await sleeper_service.get_player_stints_with_performance(league_id, player_id)