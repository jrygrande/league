import httpx
import asyncio
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
            response.raise_for_status()
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


async def get_all_player_weekly_stats_for_season(season: str):
    tasks = [get_player_weekly_stats(season, week) for week in range(1, 19)]
    weekly_stats_results = await asyncio.gather(*tasks, return_exceptions=True)

    all_stats = {}
    for i, weekly_stats in enumerate(weekly_stats_results):
        if isinstance(weekly_stats, dict):
            for player_id, stats in weekly_stats.items():
                if player_id not in all_stats:
                    all_stats[player_id] = {}
                all_stats[player_id][i + 1] = stats

    return all_stats


async def get_player_aggregated_stats(player_id: str, season: str):
    all_season_total_stats_by_player = await get_all_player_weekly_stats_for_season(season)

    total_points = 0.0
    games_played = 0

    player_total_stats = all_season_total_stats_by_player.get(player_id)

    if player_total_stats:
        for week, stats in player_total_stats.items():
            if isinstance(stats, dict):
                total_points += stats.get("pts_ppr", 0)
                if stats.get("gp", 0) > 0:
                    games_played += 1

    avg_ppg = total_points / games_played if games_played > 0 else 0.0

    return {
        "player_id": player_id,
        "season": season,
        "total_points": round(total_points, 2),
        "avg_ppg": round(avg_ppg, 2),
    }


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


async def get_all_league_transactions(league_id: str):
    transaction_tasks = [get_league_transactions(league_id, week) for week in range(1, 19)]
    weekly_transactions_results = await asyncio.gather(*transaction_tasks, return_exceptions=True)

    all_transactions = []
    for result in weekly_transactions_results:
        if isinstance(result, list):
            all_transactions.extend(result)
        # Optionally log other exceptions if needed

    return all_transactions


async def _get_single_season_lifecycle(league_id: str, player_id: str):
    league_drafts = await get_league_drafts(league_id)
    transactions = await get_all_league_transactions(league_id)
    lifecycle = []

    for draft in league_drafts:
        draft_id = draft.get("draft_id")
        if not draft_id:
            continue
        picks = await get_draft_picks(draft_id)
        for pick in picks:
            if pick.get("player_id") == player_id:
                lifecycle.append({
                    "type": f"{draft.get('type', 'unknown')} draft",
                    "timestamp": None,
                    "details": {
                        "roster_id": pick.get("roster_id"),
                        "round": pick.get("round"),
                        "pick": pick.get("pick_no"),
                        "draft_id": draft_id,
                        "season": draft.get("season"),
                    },
                })

    for tx in transactions:
        is_involved = False
        if tx.get("adds") and player_id in tx.get("adds", {}):
            is_involved = True
        if tx.get("drops") and player_id in tx.get("drops", {}):
            is_involved = True
        if is_involved:
            lifecycle.append({
                "type": tx.get("type"),
                "timestamp": tx.get("status_updated"),
                "details": {
                    "transaction_id": tx.get("transaction_id"),
                    "roster_ids": tx.get("roster_ids"),
                    "adds": tx.get("adds"),
                    "drops": tx.get("drops"),
                },
            })
    return lifecycle


async def get_player_lifecycle(league_id: str, player_id: str):
    history = await get_league_history(league_id)
    tasks = [
        _get_single_season_lifecycle(season.get("league_id"), player_id)
        for season in history
        if season.get("league_id")
    ]
    seasonal_lifecycles = await asyncio.gather(*tasks)

    full_lifecycle = []
    for season_events in seasonal_lifecycles:
        full_lifecycle.extend(season_events)

    full_lifecycle.sort(key=lambda x: x.get("timestamp") or 0)
    return full_lifecycle


async def get_roster_analysis(league_id: str, roster_id: int):
    rosters = await get_league_rosters(league_id)
    all_players_map = await get_all_players()

    target_roster = next((r for r in rosters if r.get("roster_id") == roster_id), None)

    if not target_roster or not target_roster.get("players"):
        return []

    player_ids = target_roster.get("players")
    semaphore = asyncio.Semaphore(5)

    async def get_player_acquisition(player_id):
        async with semaphore:
            try:
                lifecycle = await get_player_lifecycle(league_id, player_id)
                player_info = all_players_map.get(player_id, {})
                acquisition_event = lifecycle[-1] if lifecycle else None

                timestamp = acquisition_event.get("timestamp") if acquisition_event else None
                acquisition_method = acquisition_event.get("type") if acquisition_event else "unknown"
                acquisition_details = acquisition_event.get("details") if acquisition_event else {}

                acquisition_date = None
                if timestamp:
                    acquisition_date = datetime.fromtimestamp(timestamp / 1000).isoformat()
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
                return {"player_id": player_id, "error": f"An error occurred: {repr(e)}"}

    analysis_tasks = [get_player_acquisition(pid) for pid in player_ids]
    return await asyncio.gather(*analysis_tasks)

async def get_league_matchups(league_id: str, week: int):
    url = f"{API_URL}/league/{league_id}/matchups/{week}"
    return await get(url)


async def get_all_league_matchups(league_id: str):
    matchup_tasks = [get_league_matchups(league_id, week) for week in range(1, 19)]
    weekly_matchups_results = await asyncio.gather(*matchup_tasks, return_exceptions=True)

    all_matchups = []
    for result in weekly_matchups_results:
        if isinstance(result, list):
            all_matchups.extend(result)
    return all_matchups

from datetime import datetime, timedelta

def get_week_start_date(season: int, week: int) -> datetime:
    # This is a simplified approximation. NFL seasons typically start in early September.
    # Week 1 is usually the first full week of games.
    # For simplicity, we'll assume Sept 1st of the season year is a good approximation for week 1 start.
    # A more accurate implementation would involve actual NFL schedule data.
    return datetime(season, 9, 1) + timedelta(weeks=week - 1)

async def get_player_performance_since_transaction(league_id: str, player_id: str, transaction_id: str):
    # 1. Get the full league history
    league_history = await get_league_history(league_id)
    if not league_history:
        return {"error": f"Could not find league history for league {league_id}"}

    # 2. Fetch all transactions from all seasons in the league's history
    transaction_tasks = [get_all_league_transactions(season["league_id"]) for season in league_history]
    all_seasons_transactions = await asyncio.gather(*transaction_tasks)
    all_transactions = [tx for season_txs in all_seasons_transactions for tx in season_txs]

    # 3. Find the target transaction and its timestamp
    target_transaction = next((tx for tx in all_transactions if tx.get("transaction_id") == transaction_id), None)
    if not target_transaction:
        return {"error": f"Transaction {transaction_id} not found in the history of league {league_id}"}
    transaction_timestamp_ms = target_transaction.get("status_updated")
    transaction_date = datetime.fromtimestamp(transaction_timestamp_ms / 1000)

    # 4. Get player data across all seasons
    seasons = [league.get("season") for league in league_history if league.get("season")]
    stats_tasks = [get_all_player_weekly_stats_for_season(season) for season in seasons]
    matchup_tasks = [get_all_league_matchups(season_league["league_id"]) for season_league in league_history]

    all_seasons_stats_results = await asyncio.gather(*stats_tasks)
    all_seasons_matchups_results = await asyncio.gather(*matchup_tasks)

    # 5. Flatten the data for easier processing
    player_weekly_stats = {}
    for i, season_year in enumerate(seasons):
        season_stats = all_seasons_stats_results[i]
        if player_id in season_stats:
            for week, stats in season_stats[player_id].items():
                if isinstance(stats, dict):
                    stats['season'] = season_year
                    stats['week'] = week
                    player_weekly_stats[f"{season_year}-{week}"] = stats

    all_matchups = [matchup for season_matchups in all_seasons_matchups_results for matchup in season_matchups]

    # 6. Analyze the player's performance week by week
    analysis = {
        "before_trade": {"active": {}, "inactive": {}},
        "after_trade": {"active": {}, "inactive": {}},
    }

    for week_str, stats in player_weekly_stats.items():
        if not stats: # Filter out empty stats
            continue

        season_year = stats.get("season")
        week = stats.get("week")
        week_timestamp = get_week_start_date(int(season_year), int(week))

        period = "before_trade" if week_timestamp < transaction_date else "after_trade"
        
        player_status = "inactive"
        if stats.get("gp", 0) > 0: # If games played > 0, player was active
            player_status = "active"
        
        if season_year not in analysis[period][player_status]:
            analysis[period][player_status][season_year] = []
        analysis[period][player_status][season_year].append(stats)

    # 7. Summarize the results
    summary = {}
    for period, data in analysis.items():
        summary[period] = {"overall": {}, "breakdown_by_season": {}}
        for status, season_data in data.items():
            total_points_overall = 0
            games_played_overall = 0
            
            for season_year, weekly_scores in season_data.items():
                total_points_season = sum(s.get("pts_ppr", 0) for s in weekly_scores if s)
                games_played_season = len(weekly_scores)
                avg_ppg_season = total_points_season / games_played_season if games_played_season > 0 else 0
                
                summary[period]["breakdown_by_season"][f"{status}_{season_year}"] = {
                    "games_played": games_played_season,
                    "total_points": round(total_points_season, 2),
                    "avg_ppg": round(avg_ppg_season, 2),
                }
                total_points_overall += total_points_season
                games_played_overall += games_played_season
            
            avg_ppg_overall = total_points_overall / games_played_overall if games_played_overall > 0 else 0
            summary[period]["overall"][status] = {
                "games_played": games_played_overall,
                "total_points": round(total_points_overall, 2),
                "avg_ppg": round(avg_ppg_overall, 2),
            }

    return {
        "player_id": player_id,
        "transaction_id": transaction_id,
        "transaction_date": transaction_date.isoformat(),
        "summary": summary,
    }


    return all_matchups

async def get_player_performance_between_transactions(league_id: str, player_id: str, transaction_id_x: str, transaction_id_y: str):
    # 1. Get the full league history
    league_history = await get_league_history(league_id)
    if not league_history:
        return {"error": f"Could not find league history for league {league_id}"}

    # 2. Fetch all transactions from all seasons in the league's history
    transaction_tasks = [get_all_league_transactions(season["league_id"]) for season in league_history]
    all_seasons_transactions = await asyncio.gather(*transaction_tasks)
    all_transactions = [tx for season_txs in all_seasons_transactions for tx in season_txs]

    # 3. Find the target transactions and their timestamps
    target_transaction_x = next((tx for tx in all_transactions if tx.get("transaction_id") == transaction_id_x), None)
    if not target_transaction_x:
        return {"error": f"Transaction {transaction_id_x} not found in the history of league {league_id}"}
    transaction_date_x = datetime.fromtimestamp(target_transaction_x.get("status_updated") / 1000)

    target_transaction_y = next((tx for tx in all_transactions if tx.get("transaction_id") == transaction_id_y), None)
    if not target_transaction_y:
        return {"error": f"Transaction {transaction_id_y} not found in the history of league {league_id}"}
    transaction_date_y = datetime.fromtimestamp(target_transaction_y.get("status_updated") / 1000)

    # Ensure transaction_date_x is before transaction_date_y
    if transaction_date_x > transaction_date_y:
        transaction_date_x, transaction_date_y = transaction_date_y, transaction_date_x
        transaction_id_x, transaction_id_y = transaction_id_y, transaction_id_x

    # 4. Get player data across all seasons
    seasons = [league.get("season") for league in league_history if league.get("season")]
    stats_tasks = [get_all_player_weekly_stats_for_season(season) for season in seasons]
    matchup_tasks = [get_all_league_matchups(season_league["league_id"]) for season_league in league_history]

    all_seasons_stats_results = await asyncio.gather(*stats_tasks)
    all_seasons_matchups_results = await asyncio.gather(*matchup_tasks)

    # 5. Flatten the data for easier processing
    player_weekly_stats = {}
    for i, season_year in enumerate(seasons):
        season_stats = all_seasons_stats_results[i]
        if player_id in season_stats:
            for week, stats in season_stats[player_id].items():
                if isinstance(stats, dict):
                    stats['season'] = season_year
                    stats['week'] = week
                    player_weekly_stats[f"{season_year}-{week}"] = stats

    all_matchups = [matchup for season_matchups in all_seasons_matchups_results for matchup in season_matchups]

    # 6. Analyze the player's performance week by week
    analysis = {
        "between_transactions": {"active": {}, "inactive": {}},
    }

    for week_str, stats in player_weekly_stats.items():
        if not stats: # Filter out empty stats
            continue

        season_year = stats.get("season")
        week = stats.get("week")
        week_timestamp = get_week_start_date(int(season_year), int(week))

        if transaction_date_x <= week_timestamp <= transaction_date_y:
            player_status = "inactive"
            if stats.get("gp", 0) > 0: # If games played > 0, player was active
                player_status = "active"
            
            if season_year not in analysis["between_transactions"][player_status]:
                analysis["between_transactions"][player_status][season_year] = []
            analysis["between_transactions"][player_status][season_year].append(stats)

    # 7. Summarize the results
    summary = {}
    for period, data in analysis.items():
        summary[period] = {"overall": {}, "breakdown_by_season": {}}
        for status, season_data in data.items():
            total_points_overall = 0
            games_played_overall = 0
            
            for season_year, weekly_scores in season_data.items():
                total_points_season = sum(s.get("pts_ppr", 0) for s in weekly_scores if s)
                games_played_season = len(weekly_scores)
                avg_ppg_season = total_points_season / games_played_season if games_played_season > 0 else 0
                
                summary[period]["breakdown_by_season"][f"{status}_{season_year}"] = {
                    "games_played": games_played_season,
                    "total_points": round(total_points_season, 2),
                    "avg_ppg": round(avg_ppg_season, 2),
                }
                total_points_overall += total_points_season
                games_played_overall += games_played_season
            
            avg_ppg_overall = total_points_overall / games_played_overall if games_played_overall > 0 else 0
            summary[period]["overall"][status] = {
                "games_played": games_played_overall,
                "total_points": round(total_points_overall, 2),
                "avg_ppg": round(avg_ppg_overall, 2),
            }

    return {
        "player_id": player_id,
        "transaction_id_x": transaction_id_x,
        "transaction_id_y": transaction_id_y,
        "transaction_date_x": transaction_date_x.isoformat(),
        "transaction_date_y": transaction_date_y.isoformat(),
        "summary": summary,
    }

