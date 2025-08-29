import httpx
import asyncio
from fastapi import HTTPException
import json
import os
from datetime import datetime

API_URL = "https://api.sleeper.app/v1"


async def get_user_by_username(username: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_URL}/user/{username}")
        response.raise_for_status()
        return response.json()


async def get_leagues_for_user(user_id: str, season: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_URL}/user/{user_id}/leagues/nfl/{season}")
        response.raise_for_status()
        return response.json()


async def get_league_drafts(league_id: str):
    if league_id in _drafts_cache:
        return _drafts_cache[league_id]

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_URL}/league/{league_id}/drafts")
        response.raise_for_status()
        drafts = response.json()
        _drafts_cache[league_id] = drafts
        return drafts


async def get_league_rosters(league_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_URL}/league/{league_id}/rosters")
        response.raise_for_status()
        return response.json()


asyncd_draft_picks_cache = {}


async def get_draft_picks(draft_id: str):
    if draft_id in _draft_picks_cache:
        return _draft_picks_cache[draft_id]

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_URL}/draft/{draft_id}/picks")
        response.raise_for_status()
        picks = response.json()
        _draft_picks_cache[draft_id] = picks
        return picks


async def get_league_transactions(league_id: str, week: int):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_URL}/league/{league_id}/transactions/{week}")
        response.raise_for_status()
        return response.json()


_players_cache = None
_drafts_cache = {}
_transactions_cache = {}
_draft_picks_cache = {}


PLAYERS_CACHE_FILE = "players.json"


async def get_all_players():
    global _players_cache
    if _players_cache:
        return _players_cache

    if os.path.exists(PLAYERS_CACHE_FILE):
        with open(PLAYERS_CACHE_FILE, "r") as f:
            _players_cache = json.load(f)
            return _players_cache

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_URL}/players/nfl")
        response.raise_for_status()
        players_data = response.json()

        with open(PLAYERS_CACHE_FILE, "w") as f:
            json.dump(players_data, f, indent=2)

        _players_cache = players_data
        return _players_cache


async def get_league(league_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_URL}/league/{league_id}")
        response.raise_for_status()
        return response.json()


async def get_league_history(league_id: str):
    history = []
    current_league_id = league_id

    while current_league_id:
        try:
            league = await get_league(current_league_id)
            history.append(league)
            current_league_id = league.get("previous_league_id")
        except httpx.HTTPStatusError:
            # If a league in the chain is not found (e.g., 404), stop traversing.
            break

    if not history:
        raise HTTPException(
            status_code=404, detail=f"Could not find the base league with ID {league_id}."
        )

    return history


async def get_all_league_transactions(league_id: str):
    if league_id in _transactions_cache:
        return _transactions_cache[league_id]

    transaction_tasks = []
    for week in range(1, 19):  # NFL season has 18 weeks
        transaction_tasks.append(get_league_transactions(league_id, week))

    weekly_transactions = await asyncio.gather(*transaction_tasks)

    all_transactions = []
    for weekly_list in weekly_transactions:
        all_transactions.extend(weekly_list)

    _transactions_cache[league_id] = all_transactions
    return all_transactions


async def _get_single_season_lifecycle(league_id: str, player_id: str):
    """Helper to get the player lifecycle for a single season."""
    league_drafts = await get_league_drafts(league_id)
    transactions = await get_all_league_transactions(league_id)

    lifecycle = []

    # Find draft event by fetching picks for each draft
    for draft in league_drafts:
        draft_id = draft.get("draft_id")
        if not draft_id:
            continue

        picks = await get_draft_picks(draft_id)
        for pick in picks:
            if pick.get("player_id") == player_id:
                lifecycle.append(
                    {
                        "type": f"{draft.get('type', 'unknown')} draft",
                        "timestamp": None,
                        "details": {
                            "roster_id": pick.get("roster_id"),
                            "round": pick.get("round"),
                            "pick": pick.get("pick_no"),
                            "draft_id": draft_id,
                            "season": draft.get("season"),
                        },
                    }
                )

    # Find transaction events
    for tx in transactions:
        is_involved = False
        if tx.get("adds") and player_id in tx.get("adds", {}):
            is_involved = True
        if tx.get("drops") and player_id in tx.get("drops", {}):
            is_involved = True

        if is_involved:
            lifecycle.append(
                {
                    "type": tx.get("type"),
                    "timestamp": tx.get("status_updated"),
                    "details": {
                        "transaction_id": tx.get("transaction_id"),
                        "roster_ids": tx.get("roster_ids"),
                        "adds": tx.get("adds"),
                        "drops": tx.get("drops"),
                    },
                }
            )

    return lifecycle


async def get_player_lifecycle(league_id: str, player_id: str):
    """Gets the full, multi-year lifecycle for a player in a league."""
    history = await get_league_history(league_id)

    tasks = []
    for season in history:
        season_league_id = season.get("league_id")
        if season_league_id:
            tasks.append(_get_single_season_lifecycle(season_league_id, player_id))

    seasonal_lifecycles = await asyncio.gather(*tasks)

    full_lifecycle = []
    for season_events in seasonal_lifecycles:
        full_lifecycle.extend(season_events)

    # Sort the final combined list of all events from all seasons
    full_lifecycle.sort(key=lambda x: x.get("timestamp") or 0)

    return full_lifecycle


async def get_roster_analysis(league_id: str, roster_id: int):
    rosters = await get_league_rosters(league_id)
    all_players_map = await get_all_players()

    target_roster = None
    for r in rosters:
        if r.get("roster_id") == roster_id:
            target_roster = r
            break

    if not target_roster or not target_roster.get("players"):
        return []

    player_ids = target_roster.get("players")
    semaphore = asyncio.Semaphore(5)  # Limit concurrency to 5

    async def get_player_acquisition(player_id):
        async with semaphore:
            try:
                lifecycle = await get_player_lifecycle(league_id, player_id)
                player_info = all_players_map.get(player_id, {})
                acquisition_event = lifecycle[-1] if lifecycle else None

                timestamp = acquisition_event.get("timestamp") if acquisition_event else None
                acquisition_method = (
                    acquisition_event.get("type") if acquisition_event else "unknown"
                )
                acquisition_details = (
                    acquisition_event.get("details") if acquisition_event else {}
                )

                acquisition_date = None
                if timestamp:
                    acquisition_date = datetime.fromtimestamp(
                        timestamp / 1000
                    ).isoformat()
                elif "draft" in acquisition_method:
                    season = acquisition_details.get("season")
                    if season:
                        acquisition_date = f"{season}-06-01T00:00:00"

                return {
                    "player_id": player_id,
                    "first_name": player_info.get("first_name"),
                    "last_name": player_info.get("last_name"),
                    "position": player_info.get("position"),
                    "acquisition_method": acquisition_method,
                    "acquisition_date": acquisition_date,
                    "acquisition_details": acquisition_details,
                }
            except Exception as e:
                return {
                    "player_id": player_id,
                    "error": f"An error occurred during analysis: {repr(e)}",
                }

    analysis_tasks = [get_player_acquisition(pid) for pid in player_ids]
    roster_analysis = await asyncio.gather(*analysis_tasks)

    return roster_analysis


