import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any


from .. import client
from ..models.sleeper import (
    League,
    Roster,
    Draft,
    Pick,
    Player,
    Stats,
    Transaction,
    Matchup,
)

# These constants will eventually move to config.py
API_URL = "https://api.sleeper.app/v1"
CACHE_TTL_SECONDS = 604800  # 7 days


async def get_all_player_weekly_stats_for_season(season: str) -> Dict[str, Dict[int, Stats]]:
    tasks = [client.get_player_weekly_stats(season, week) for week in range(1, 19)]
    weekly_stats_results = await asyncio.gather(*tasks, return_exceptions=True)

    all_stats: Dict[str, Dict[int, Stats]] = {}
    for i, weekly_stats_data in enumerate(weekly_stats_results):
        if isinstance(weekly_stats_data, dict):
            for player_id, stats_data in weekly_stats_data.items():
                if player_id not in all_stats:
                    all_stats[player_id] = {}
                # Ensure stats_data is a dictionary before passing to Stats
                if isinstance(stats_data, dict):
                    all_stats[player_id][i + 1] = Stats(player_id=player_id, week=i + 1, season=season, **stats_data)

    return all_stats


async def get_player_aggregated_stats(player_id: str, season: str) -> Dict[str, Any]:
    all_season_total_stats_by_player = await get_all_player_weekly_stats_for_season(season)

    total_points = 0.0
    games_played = 0

    player_total_stats = all_season_total_stats_by_player.get(player_id)

    if player_total_stats:
        for week, stats in player_total_stats.items():
            # stats is already a Stats object
            total_points += stats.pts_ppr if stats.pts_ppr is not None else 0
            if stats.gp is not None and stats.gp > 0:
                games_played += 1

    avg_ppg = total_points / games_played if games_played > 0 else 0.0

    return {
        "player_id": player_id,
        "season": season,
        "total_points": round(total_points, 2),
        "avg_ppg": round(avg_ppg, 2),
    }


async def get_all_league_transactions(league_id: str) -> List[Transaction]:
    transaction_tasks = [client.get_league_transactions(league_id, week) for week in range(1, 19)]
    weekly_transactions_results = await asyncio.gather(*transaction_tasks, return_exceptions=True)

    all_transactions: List[Transaction] = []
    for result in weekly_transactions_results:
        if isinstance(result, list):
            for tx_data in result:
                all_transactions.append(Transaction(**tx_data))
        # Optionally log other exceptions if needed

    return all_transactions


async def _get_single_season_lifecycle(league_id: str, player_id: str) -> List[Dict[str, Any]]:
    league_drafts_data = await client.get_league_drafts(league_id)
    league_drafts = [Draft(**d) for d in league_drafts_data] if league_drafts_data else []

    transactions = await get_all_league_transactions(league_id)
    lifecycle = []

    for draft in league_drafts:
        draft_id = draft.draft_id
        if not draft_id:
            continue
        picks_data = await client.get_draft_picks(draft_id)
        picks = [Pick(**p) for p in picks_data] if picks_data else []
        for pick in picks:
            if pick.player_id == player_id:
                lifecycle.append({
                    "type": f"{draft.type} draft",
                    "timestamp": None,
                    "details": {
                        "roster_id": pick.roster_id,
                        "round": pick.round,
                        "pick": pick.pick_no,
                        "draft_id": draft_id,
                        "season": draft.season,
                    },
                })

    for tx in transactions:
        is_involved = False
        if tx.adds and player_id in tx.adds:
            is_involved = True
        if tx.drops and player_id in tx.drops:
            is_involved = True
        if is_involved:
            lifecycle.append({
                "type": tx.type,
                "timestamp": tx.status_updated,
                "details": {
                    "transaction_id": tx.transaction_id,
                    "roster_ids": tx.roster_ids,
                    "adds": tx.adds,
                    "drops": tx.drops,
                },
            })
    return lifecycle


async def get_player_lifecycle(league_id: str, player_id: str) -> List[Dict[str, Any]]:
    history_data = await client.get_league_history(league_id)
    history = [League(**item) for item in history_data] if history_data else []

    tasks = [
        _get_single_season_lifecycle(season.league_id, player_id)
        for season in history
        if season.league_id
    ]
    seasonal_lifecycles = await asyncio.gather(*tasks)

    full_lifecycle = []
    for season_events in seasonal_lifecycles:
        full_lifecycle.extend(season_events)

    full_lifecycle.sort(key=lambda x: x.get("timestamp") or 0)
    return full_lifecycle


async def get_roster_analysis(league_id: str, roster_id: int) -> List[Dict[str, Any]]:
    rosters_data = await client.get_league_rosters(league_id)
    rosters = [Roster(**r) for r in rosters_data] if rosters_data else []

    all_players_map_data = await client.get_all_players()
    all_players_map = {p_id: Player(**p_data) for p_id, p_data in all_players_map_data.items()} if all_players_map_data else {}

    target_roster = next((r for r in rosters if r.roster_id == roster_id), None)

    if not target_roster or not target_roster.players:
        return []

    player_ids = target_roster.players
    semaphore = asyncio.Semaphore(5)

    async def get_player_acquisition(player_id):
        async with semaphore:
            try:
                lifecycle = await get_player_lifecycle(league_id, player_id)
                player_info = all_players_map.get(player_id) # This is already a Player object or None
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
                    "first_name": player_info.first_name if player_info else None,
                    "last_name": player_info.last_name if player_info else None,
                    "position": player_info.position if player_info else None,
                    "acquisition_method": acquisition_method,
                    "acquisition_date": acquisition_date,
                    "acquisition_details": acquisition_details,
                }
            except Exception as e:
                return {"player_id": player_id, "error": f"An error occurred: {repr(e)}"}

    analysis_tasks = [get_player_acquisition(pid) for pid in player_ids]
    return await asyncio.gather(*analysis_tasks)


async def get_all_league_matchups(league_id: str) -> List[Matchup]:
    matchup_tasks = [client.get_league_matchups(league_id, week) for week in range(1, 19)]
    weekly_matchups_results = await asyncio.gather(*matchup_tasks, return_exceptions=True)

    all_matchups: List[Matchup] = []
    for result in weekly_matchups_results:
        if isinstance(result, list):
            for matchup_data in result:
                all_matchups.append(Matchup(**matchup_data))
    return all_matchups


def get_week_start_date(season: int, week: int) -> datetime:
    # This is a simplified approximation. NFL seasons typically start in early September.
    # Week 1 is usually the first full week of games.
    # For simplicity, we'll assume Sept 1st of the season year is a good approximation for week 1 start.
    # A more accurate implementation would involve actual NFL schedule data.
    return datetime(season, 9, 1) + timedelta(weeks=week - 1)


async def get_player_performance_since_transaction(league_id: str, player_id: str, transaction_id: str) -> Dict[str, Any]:
    # 1. Get the full league history
    league_history_data = await client.get_league_history(league_id)
    league_history = [League(**item) for item in league_history_data] if league_history_data else []

    if not league_history:
        return {"error": f"Could not find league history for league {league_id}"}

    # 2. Fetch all transactions from all seasons in the league's history
    transaction_tasks = [get_all_league_transactions(season.league_id) for season in league_history]
    all_seasons_transactions = await asyncio.gather(*transaction_tasks)
    all_transactions = [tx for season_txs in all_seasons_transactions for tx in season_txs]

    # 3. Find the target transaction and its timestamp
    target_transaction = next((tx for tx in all_transactions if tx.transaction_id == transaction_id), None)
    if not target_transaction:
        return {"error": f"Transaction {transaction_id} not found in the history of league {league_id}"}
    transaction_timestamp_ms = target_transaction.status_updated
    transaction_date = datetime.fromtimestamp(transaction_timestamp_ms / 1000) if transaction_timestamp_ms else datetime.min # Handle None

    # 4. Get player data across all seasons
    seasons = [league.season for league in league_history if league.season]
    stats_tasks = [get_all_player_weekly_stats_for_season(season) for season in seasons]
    matchup_tasks = [client.get_league_matchups(season_league.league_id) for season_league in league_history]

    all_seasons_stats_results = await asyncio.gather(*stats_tasks)
    await asyncio.gather(*matchup_tasks) # Removed assignment to all_seasons_matchup_results

    # 5. Flatten the data for easier processing
    player_weekly_stats: Dict[str, Stats] = {}
    for i, season_year in enumerate(seasons):
        season_stats = all_seasons_stats_results[i]
        if player_id in season_stats:
            for week, stats in season_stats[player_id].items():
                player_weekly_stats[f"{season_year}-{week}"] = stats

    # 6. Analyze the player's performance week by week
    analysis = {
        "before_trade": {"active": {}, "inactive": {}},
        "after_trade": {"active": {}, "inactive": {}},
    }

    for week_str, stats in player_weekly_stats.items():
        if not stats: # Filter out empty stats
            continue

        season_year = stats.season
        week = stats.week
        week_timestamp = get_week_start_date(int(season_year), int(week))

        period = "before_trade" if week_timestamp < transaction_date else "after_trade"

        player_status = "inactive"
        if stats.gp is not None and stats.gp > 0: # If games played > 0, player was active
            player_status = "active"

        if season_year not in analysis[period][player_status]:
            analysis[period][player_status][season_year] = []
        analysis[period][player_status][season_year].append(stats.dict()) # Convert Pydantic model back to dict for analysis

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
        "transaction_date": transaction_date.isoformat() if transaction_date != datetime.min else None,
        "summary": summary,
    }


async def get_player_performance_between_transactions(league_id: str, player_id: str, transaction_id_x: str, transaction_id_y: str) -> Dict[str, Any]:
    # 1. Get the full league history
    league_history_data = await client.get_league_history(league_id)
    league_history = [League(**item) for item in league_history_data] if league_history_data else []
    if not league_history:
        return {"error": f"Could not find league history for league {league_id}"}

    # 2. Fetch all transactions from all seasons in the league's history
    transaction_tasks = [get_all_league_transactions(season.league_id) for season in league_history]
    all_seasons_transactions = await asyncio.gather(*transaction_tasks)
    all_transactions = [tx for season_txs in all_seasons_transactions for tx in season_txs]

    # 3. Find the target transactions and their timestamps
    target_transaction_x = next((tx for tx in all_transactions if tx.transaction_id == transaction_id_x), None)
    if not target_transaction_x:
        return {"error": f"Transaction {transaction_id_x} not found in the history of league {league_id}"}
    transaction_date_x = datetime.fromtimestamp(target_transaction_x.status_updated / 1000) if target_transaction_x.status_updated else datetime.min

    target_transaction_y = next((tx for tx in all_transactions if tx.transaction_id == transaction_id_y), None)
    if not target_transaction_y:
        return {"error": f"Transaction {transaction_id_y} not found in the history of league {league_id}"}
    transaction_date_y = datetime.fromtimestamp(target_transaction_y.status_updated / 1000) if target_transaction_y.status_updated else datetime.min

    # Ensure transaction_date_x is before transaction_date_y
    if transaction_date_x > transaction_date_y:
        transaction_date_x, transaction_date_y = transaction_date_y, transaction_date_x
        transaction_id_x, transaction_id_y = transaction_id_y, transaction_id_x

    # 4. Get player data across all seasons
    seasons = [league.season for league in league_history if league.season]
    stats_tasks = [get_all_player_weekly_stats_for_season(season) for season in seasons]
    matchup_tasks = [client.get_league_matchups(season_league.league_id) for season_league in league_history]

    all_seasons_stats_results = await asyncio.gather(*stats_tasks)
    await asyncio.gather(*matchup_tasks) # Removed assignment to all_seasons_matchup_results

    # 5. Flatten the data for easier processing
    player_weekly_stats: Dict[str, Stats] = {}
    for i, season_year in enumerate(seasons):
        season_stats = all_seasons_stats_results[i]
        if player_id in season_stats:
            for week, stats in season_stats[player_id].items():
                player_weekly_stats[f"{season_year}-{week}"] = stats

    # 6. Analyze the player's performance week by week
    analysis = {
        "between_transactions": {"active": {}, "inactive": {}},
    }

    for week_str, stats in player_weekly_stats.items():
        if not stats: # Filter out empty stats
            continue

        season_year = stats.season
        week = stats.week
        week_timestamp = get_week_start_date(int(season_year), int(week))

        if transaction_date_x <= week_timestamp <= transaction_date_y:
            player_status = "inactive"
            if stats.gp is not None and stats.gp > 0: # If games played > 0, player was active
                player_status = "active"

            if season_year not in analysis["between_transactions"][player_status]:
                analysis["between_transactions"][player_status][season_year] = []
            analysis["between_transactions"][player_status][season_year].append(stats.dict()) # Convert Pydantic model back to dict for analysis

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
        "transaction_date_x": transaction_date_x.isoformat() if transaction_date_x != datetime.min else None,
        "transaction_date_y": transaction_date_y.isoformat() if transaction_date_y != datetime.min else None,
        "summary": summary,
    }