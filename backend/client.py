import httpx
import json
from datetime import datetime, timedelta

from . import database


API_URL = "https://api.sleeper.app/v1"
CACHE_TTL_SECONDS = 604800  # 7 days


async def get(url: str):
    """
    A generic, caching GET request for the Sleeper API.
    """
    db = await database.get_db_connection()
    try:
        # 1. Check cache
        cursor = await db.execute("SELECT data, timestamp FROM api_cache WHERE url = ?", (url,))
        row = await cursor.fetchone()

        if row:
            cached_data = json.loads(row["data"])
            timestamp = datetime.fromisoformat(row["timestamp"])
            if datetime.utcnow() - timestamp < timedelta(seconds=CACHE_TTL_SECONDS):
                return cached_data

        # 2. If not in cache or stale, fetch from API
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            # Do NOT raise_for_status() here. Handle 404 specifically in calling functions.
            # response.raise_for_status()
            
            if response.status_code == 404:
                return None # Return None for 404 Not Found

            response.raise_for_status() # Raise for other errors (e.g., 5xx)
            fresh_data = response.json()

            # 3. Store in cache
            await db.execute(
                "INSERT OR REPLACE INTO api_cache (url, data, timestamp) VALUES (?, ?, ?)",
                (url, json.dumps(fresh_data), datetime.utcnow().isoformat()),
            )
            await db.commit()
            return fresh_data

    finally:
        await db.close()


async def get_user_by_username(username: str):
    url = f"{API_URL}/user/{username}"
    return await get(url)


async def get_leagues_for_user(user_id: str, season: str):
    url = f"{API_URL}/user/{user_id}/leagues/nfl/{season}"
    return await get(url)


async def get_league_drafts(league_id: str):
    url = f"{API_URL}/league/{league_id}/drafts"
    return await get(url)


async def get_league_rosters(league_id: str):
    url = f"{API_URL}/league/{league_id}/rosters"
    return await get(url)


async def get_draft_picks(draft_id: str):
    url = f"{API_URL}/draft/{draft_id}/picks"
    return await get(url)


async def get_player_weekly_stats(season: str, week: int):
    url = f"{API_URL}/stats/nfl/regular/{season}/{week}"
    # This endpoint can return 404 for old seasons, handle it gracefully
    try:
        return await get(url)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {}
        raise


async def get_league_transactions(league_id: str, week: int):
    url = f"{API_URL}/league/{league_id}/transactions/{week}"
    try:
        return await get(url)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return []
        raise


async def get_all_players():
    url = f"{API_URL}/players/nfl"
    return await get(url)


async def get_league(league_id: str):
    url = f"{API_URL}/league/{league_id}"
    return await get(url)


async def get_league_history(league_id: str):
    history = []
    current_league_id = league_id

    while current_league_id:
        try:
            league = await get_league(current_league_id)
            history.append(league)
            current_league_id = league.get("previous_league_id")
        except httpx.HTTPStatusError:
            break  # Stop if a league in the chain is not found

    return history


async def get_league_matchups(league_id: str, week: int):
    url = f"{API_URL}/league/{league_id}/matchups/{week}"
    return await get(url)