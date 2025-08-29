from fastapi import FastAPI

from . import client

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/user/{username}")
async def get_user(username: str):
    return await client.get_user_by_username(username)


@app.get("/user/{username}/leagues/{season}")
async def get_leagues_for_user(username: str, season: str):
    user = await client.get_user_by_username(username)
    user_id = user["user_id"]
    return await client.get_leagues_for_user(user_id, season)


@app.get("/league/{league_id}/drafts")
async def get_league_drafts(league_id: str):
    return await client.get_league_drafts(league_id)


@app.get("/league/{league_id}/rosters")
async def get_league_rosters(league_id: str):
    return await client.get_league_rosters(league_id)


@app.get("/league/{league_id}/transactions/{week}")
async def get_league_transactions(league_id: str, week: int):
    return await client.get_league_transactions(league_id, week)


@app.get("/players")
async def get_all_players():
    return await client.get_all_players()


@app.get("/league/{league_id}/history")
async def get_league_history(league_id: str):
    return await client.get_league_history(league_id)


@app.get("/league/{league_id}/transactions")
async def get_all_league_transactions(league_id: str):
    return await client.get_all_league_transactions(league_id)


@app.get("/league/{league_id}/player/{player_id}/lifecycle")
async def get_player_lifecycle(league_id: str, player_id: str):
    return await client.get_player_lifecycle(league_id, player_id)


@app.get("/league/{league_id}/roster/{roster_id}/analysis")
async def get_roster_analysis(league_id: str, roster_id: int):
    return await client.get_roster_analysis(league_id, roster_id)


@app.get("/stats/nfl/{season}")
async def get_nfl_player_stats(season: str):
    return await client.get_player_weekly_stats(season)


@app.get("/player/{player_id}/aggregated_stats/{season}")
async def get_player_aggregated_stats(player_id: str, season: str):
    return await client.get_player_aggregated_stats(player_id, season)
