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
    PlayerStint,
    DraftPickInfo,
    DraftPickOwnership,
    TradeAsset,
    TradeNode,
    TradeTree,
    TradedPick,
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


async def get_single_season_transactions(league_id: str) -> List[Transaction]:
    """Get all transactions for a single season (league ID)."""
    transaction_tasks = [client.get_league_transactions(league_id, week) for week in range(1, 19)]
    weekly_transactions_results = await asyncio.gather(*transaction_tasks, return_exceptions=True)

    all_transactions: List[Transaction] = []
    for result in weekly_transactions_results:
        if isinstance(result, list):
            for tx_data in result:
                tx_data["league_id"] = league_id
                all_transactions.append(Transaction(**tx_data))
        # Optionally log other exceptions if needed

    return all_transactions


async def get_all_league_transactions(league_id: str) -> List[Transaction]:
    """Get all transactions across all seasons in the league's history."""
    # Get the full league history
    league_history_data = await client.get_league_history(league_id)
    league_history = [League(**item) for item in league_history_data] if league_history_data else []
    
    if not league_history:
        # Fallback to single season if no history available
        return await get_single_season_transactions(league_id)
    
    # Fetch transactions from all seasons in parallel
    transaction_tasks = [get_single_season_transactions(season_league.league_id) for season_league in league_history]
    all_seasons_transactions = await asyncio.gather(*transaction_tasks, return_exceptions=True)
    
    # Flatten all transactions from all seasons
    all_transactions = []
    for season_transactions in all_seasons_transactions:
        if isinstance(season_transactions, list):
            all_transactions.extend(season_transactions)
    
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
    for i, result in enumerate(weekly_matchups_results):
        if isinstance(result, list):
            for matchup_data in result:
                matchup_data["league_id"] = league_id
                matchup_data["week"] = i + 1
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
    all_transactions = await get_all_league_transactions(league_id)

    # 3. Find the target transaction and its timestamp
    target_transaction = next((tx for tx in all_transactions if tx.transaction_id == transaction_id), None)
    if not target_transaction:
        return {"error": f"Transaction {transaction_id} not found in the history of league {league_id}"}
    transaction_timestamp_ms = target_transaction.status_updated
    transaction_date = datetime.fromtimestamp(transaction_timestamp_ms / 1000) if transaction_timestamp_ms else datetime.min # Handle None

    # 4. Get player data across all seasons
    seasons = [league.season for league in league_history if league.season]
    stats_tasks = [get_all_player_weekly_stats_for_season(season) for season in seasons]
    matchup_tasks = [get_all_league_matchups(season_league.league_id) for season_league in league_history]

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
        analysis[period][player_status][season_year].append(stats.model_dump()) # Convert Pydantic model back to dict for analysis

    # 7. Summarize the results
    summary = {}
    for period, data in analysis.items():
        summary[period] = {"overall": {}, "breakdown_by_season": {}}
        for status, season_data in data.items():
            total_points_overall = 0
            games_played_overall = 0

            for season_year, weekly_scores in season_data.items():
                total_points_season = sum(s.get("pts_ppr", 0) or 0 for s in weekly_scores if s)
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
    all_transactions = await get_all_league_transactions(league_id)

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

    # 4. Get player data across all seasons
    seasons = [league.season for league in league_history if league.season]
    stats_tasks = [get_all_player_weekly_stats_for_season(season) for season in seasons]
    matchup_tasks = [get_all_league_matchups(season_league.league_id) for season_league in league_history]

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
            analysis["between_transactions"][player_status][season_year].append(stats.model_dump()) # Convert Pydantic model back to dict for analysis

    # 7. Summarize the results
    summary = {}
    for period, data in analysis.items():
        summary[period] = {"overall": {}, "breakdown_by_season": {}}
        for status, season_data in data.items():
            total_points_overall = 0
            games_played_overall = 0

            for season_year, weekly_scores in season_data.items():
                total_points_season = sum(s.get("pts_ppr", 0) or 0 for s in weekly_scores if s)
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


async def get_player_stints_with_performance(league_id: str, player_id: str) -> List[PlayerStint]:
    # 1. Get player lifecycle events
    lifecycle_events = await get_player_lifecycle(league_id, player_id)
    
    # 2. Pre-fetch all season stats data to avoid redundant API calls
    league_history_data = await client.get_league_history(league_id)
    league_history = [League(**item) for item in league_history_data] if league_history_data else []
    
    # Get unique seasons from league history
    seasons = list(set(league.season for league in league_history if league.season))
    
    # Batch fetch all season stats in parallel
    stats_tasks = [get_all_player_weekly_stats_for_season(season) for season in seasons]
    all_seasons_stats_results = await asyncio.gather(*stats_tasks, return_exceptions=True)
    
    # Create comprehensive stats lookup: {season: {player_id: {week: Stats}}}
    all_stats_by_season = {}
    for i, season in enumerate(seasons):
        if i < len(all_seasons_stats_results) and isinstance(all_seasons_stats_results[i], dict):
            all_stats_by_season[season] = all_seasons_stats_results[i]

    # 2b. Pre-fetch matchup data for all seasons to determine starter/bench status
    matchup_tasks = [get_all_league_matchups(season_league.league_id) for season_league in league_history]
    all_seasons_matchups_results = await asyncio.gather(*matchup_tasks, return_exceptions=True)
    
    # Create matchup lookup: {season: {week: {roster_id: Matchup}}}
    all_matchups_by_season = {}
    for i, season_league in enumerate(league_history):
        season = season_league.season
        if i < len(all_seasons_matchups_results) and isinstance(all_seasons_matchups_results[i], list):
            season_matchups = all_seasons_matchups_results[i]
            all_matchups_by_season[season] = {}
            
            for matchup in season_matchups:
                week = matchup.week
                roster_id = matchup.roster_id
                
                if week not in all_matchups_by_season[season]:
                    all_matchups_by_season[season][week] = {}
                all_matchups_by_season[season][week][roster_id] = matchup

    # 3. Process events to determine stints
    stints = []
    current_stint_start_date = None
    current_roster_id = None

    # 4. Pre-fetch all roster and user data to avoid redundant API calls
    # Get all unique roster IDs from lifecycle events
    unique_roster_ids = set()
    for event in lifecycle_events:
        roster_id = event["details"].get("roster_id")
        if roster_id:
            unique_roster_ids.add(roster_id)
    
    # Batch fetch roster data from all seasons
    roster_tasks = [client.get_league_rosters(season_league.league_id) for season_league in league_history]
    all_seasons_rosters = await asyncio.gather(*roster_tasks, return_exceptions=True)
    
    # Create roster lookup: {roster_id: Roster}
    roster_lookup = {}
    unique_owner_ids = set()
    
    for season_rosters_data in all_seasons_rosters:
        if isinstance(season_rosters_data, list):
            for roster_data in season_rosters_data:
                try:
                    roster = Roster(**roster_data)
                    roster_lookup[roster.roster_id] = roster
                    if roster.owner_id:
                        unique_owner_ids.add(roster.owner_id)
                except Exception:
                    continue  # Skip invalid roster data
    
    # Batch fetch user data for all unique owners
    user_tasks = [client.get_user_by_user_id(owner_id) for owner_id in unique_owner_ids]
    all_users_data = await asyncio.gather(*user_tasks, return_exceptions=True)
    
    # Create user lookup: {owner_id: user_data}
    user_lookup = {}
    for i, owner_id in enumerate(unique_owner_ids):
        if i < len(all_users_data) and isinstance(all_users_data[i], dict):
            user_lookup[owner_id] = all_users_data[i]
    
    # Helper to get roster details and owner info (now using cached data)
    def _get_roster_info(roster_id: int):
        roster = roster_lookup.get(roster_id)
        if roster and roster.owner_id:
            user_data = user_lookup.get(roster.owner_id)
            if user_data:
                team_name = (roster.metadata or {}).get("team_name", user_data.get("display_name", user_data.get("username", "Unknown Team")))
                return {
                    "team_name": team_name,
                    "owner_username": user_data.get("username"),
                    "owner_display_name": user_data.get("display_name"),
                }
        return {"team_name": "Unknown Team", "owner_username": "Unknown", "owner_display_name": "Unknown"}

    # Iterate through sorted lifecycle events
    for i, event in enumerate(lifecycle_events):
        event_type = event["type"]
        event_timestamp = event["timestamp"]
        
        # Extract roster_id based on event type
        if "draft" in event_type:
            event_roster_id = event["details"].get("roster_id")
        elif event_type in ["trade", "waiver", "free_agent"]:
            # For trades, the new roster is in adds[player_id]
            adds = event["details"].get("adds", {})
            event_roster_id = adds.get(player_id) if adds else None
        else:
            event_roster_id = event["details"].get("roster_id")

        if "draft" in event_type or event_type == "trade" or event_type == "waiver" or event_type == "free_agent":
            # A new stint begins or an existing one changes
            if current_roster_id is None: # First event for this player
                current_stint_start_date = datetime.fromtimestamp(event_timestamp / 1000) if event_timestamp else datetime.min
                current_roster_id = event_roster_id
            elif event_roster_id != current_roster_id: # Player moved teams
                # End previous stint
                if current_stint_start_date and current_roster_id:
                    roster_info = _get_roster_info(current_roster_id)
                    stints.append(PlayerStint(
                        start_date=current_stint_start_date,
                        end_date=datetime.fromtimestamp(event_timestamp / 1000) if event_timestamp else None,
                        team_name=roster_info["team_name"],
                        owner_username=roster_info["owner_username"],
                        owner_display_name=roster_info["owner_display_name"],
                        aggregated_stats={"roster_id": current_roster_id}  # Store roster_id for matchup lookup
                    ))
                # Start new stint
                current_stint_start_date = datetime.fromtimestamp(event_timestamp / 1000) if event_timestamp else datetime.min
                current_roster_id = event_roster_id

    # Handle the last stint (player still on team)
    if current_stint_start_date and current_roster_id:
        roster_info = _get_roster_info(current_roster_id)
        stints.append(PlayerStint(
            start_date=current_stint_start_date,
            end_date=None, # Still on team
            team_name=roster_info["team_name"],
            owner_username=roster_info["owner_username"],
            owner_display_name=roster_info["owner_display_name"],
            aggregated_stats={"roster_id": current_roster_id}  # Store roster_id for matchup lookup
        ))

    # 5. Enhanced performance aggregation with starter/bench breakdown
    for stint in stints:
        roster_id = stint.aggregated_stats["roster_id"]  # Get stored roster_id
        start_year = stint.start_date.year
        end_year = stint.end_date.year if stint.end_date else datetime.now().year

        # Initialize detailed stats tracking
        starting_stats = {"total_points": 0.0, "games": 0}
        bench_stats = {"total_points": 0.0, "games": 0}
        overall_stats = {"total_points": 0.0, "games_rostered": 0, "games_active": 0, "games_started": 0}

        for year in range(start_year, end_year + 1):
            season_str = str(year)
            season_stats = all_stats_by_season.get(season_str)
            season_matchups = all_matchups_by_season.get(season_str)
            
            if not season_stats:
                continue
                
            player_season_stats = season_stats.get(player_id)
            if not player_season_stats:
                continue

            # Process each week's performance with starter/bench classification
            for week, stats in player_season_stats.items():
                week_start_date = get_week_start_date(year, week)
                
                # Only process weeks within this stint's timeframe
                if not (stint.start_date <= week_start_date and (stint.end_date is None or week_start_date < stint.end_date)):
                    continue
                
                points = stats.pts_ppr if stats.pts_ppr is not None else 0
                is_active = stats.gp is not None and stats.gp > 0
                
                # Determine starter/bench status from matchup data
                is_starting = False
                is_rostered = False
                
                if season_matchups and week in season_matchups and roster_id in season_matchups[week]:
                    matchup = season_matchups[week][roster_id]
                    is_rostered = player_id in (matchup.players or [])
                    is_starting = player_id in (matchup.starters or [])
                
                # Aggregate stats based on classification
                overall_stats["total_points"] += points
                if is_rostered:
                    overall_stats["games_rostered"] += 1
                if is_active:
                    overall_stats["games_active"] += 1
                
                if is_starting:
                    starting_stats["total_points"] += points
                    starting_stats["games"] += 1
                    overall_stats["games_started"] += 1
                elif is_rostered:  # On roster but not starting
                    bench_stats["total_points"] += points
                    bench_stats["games"] += 1
        
        # Calculate averages and build enhanced stats structure
        stint.aggregated_stats = {
            "starting": {
                "total_points": round(starting_stats["total_points"], 2),
                "games_played": starting_stats["games"],
                "avg_ppg": round(starting_stats["total_points"] / starting_stats["games"], 2) if starting_stats["games"] > 0 else 0.0
            },
            "bench": {
                "total_points": round(bench_stats["total_points"], 2),
                "games_played": bench_stats["games"],
                "avg_ppg": round(bench_stats["total_points"] / bench_stats["games"], 2) if bench_stats["games"] > 0 else 0.0
            },
            "overall": {
                "total_points": round(overall_stats["total_points"], 2),
                "games_rostered": overall_stats["games_rostered"],
                "games_active": overall_stats["games_active"],
                "games_started": overall_stats["games_started"],
                "avg_ppg": round(overall_stats["total_points"] / overall_stats["games_active"], 2) if overall_stats["games_active"] > 0 else 0.0
            }
        }

    return stints


async def get_league_draft_picks(league_id: str, season: str) -> List[DraftPickInfo]:
    """Get all draft picks for a specific league and season."""
    league_history_data = await client.get_league_history(league_id)
    league_history = [League(**item) for item in league_history_data] if league_history_data else []
    
    # Find the league for the specified season
    target_league = next((league for league in league_history if league.season == season), None)
    if not target_league:
        return []
    
    # Get drafts for that season
    drafts_data = await client.get_league_drafts(target_league.league_id)
    drafts = [Draft(**d) for d in drafts_data] if drafts_data else []
    
    all_picks = []
    for draft in drafts:
        picks_data = await client.get_draft_picks(draft.draft_id)
        if picks_data:
            for pick_data in picks_data:
                pick = DraftPickInfo(
                    draft_id=pick_data.get("draft_id"),
                    pick_no=pick_data.get("pick_no"),
                    round=pick_data.get("round"),
                    draft_slot=pick_data.get("draft_slot"),
                    player_id=pick_data.get("player_id"),
                    roster_id=pick_data.get("roster_id"),
                    picked_by=pick_data.get("picked_by"),
                    is_keeper=pick_data.get("is_keeper"),
                    metadata=pick_data.get("metadata")
                )
                all_picks.append(pick)
    
    return all_picks


def _is_draft_pick_identifier(asset_id: str) -> bool:
    """Check if an asset ID represents a draft pick."""
    # In Sleeper, draft picks are often represented as negative numbers
    # or specific patterns like "2024_1_01" (year_round_pick)
    try:
        # Check for negative numbers (common draft pick representation)
        if int(asset_id) < 0:
            return True
    except ValueError:
        pass
    
    # Check for pick identifier patterns (year_round_pick format)
    if '_' in asset_id:
        parts = asset_id.split('_')
        if len(parts) == 3:
            try:
                year = int(parts[0])
                round_num = int(parts[1])
                pick_num = int(parts[2])
                # Reasonable ranges for year, round, pick
                if 2020 <= year <= 2030 and 1 <= round_num <= 10 and 1 <= pick_num <= 20:
                    return True
            except ValueError:
                pass
    
    return False


def _parse_draft_pick_identifier(asset_id: str) -> Dict[str, Any]:
    """Parse a draft pick identifier to extract year, round, pick information."""
    pick_info = {"asset_id": asset_id, "year": None, "round": None, "pick": None}
    
    try:
        # Handle negative number format (often league-specific pick IDs)
        if int(asset_id) < 0:
            pick_info["type"] = "negative_id"
            return pick_info
    except ValueError:
        pass
    
    # Handle structured format like "2024_1_01"
    if '_' in asset_id:
        parts = asset_id.split('_')
        if len(parts) == 3:
            try:
                pick_info["year"] = int(parts[0])
                pick_info["round"] = int(parts[1])
                pick_info["pick"] = int(parts[2])
                pick_info["type"] = "structured"
                return pick_info
            except ValueError:
                pass
    
    pick_info["type"] = "unknown"
    return pick_info


async def analyze_trade_assets(transaction: Transaction, all_players_map: Dict[str, Player], league_id: str = None) -> List[TradeAsset]:
    """Analyze a trade transaction to identify all assets (players and picks) involved."""
    assets = []
    
    # Analyze adds
    if transaction.adds:
        for asset_id, roster_id in transaction.adds.items():
            if _is_draft_pick_identifier(asset_id):
                pick_info = _parse_draft_pick_identifier(asset_id)
                assets.append(TradeAsset(
                    asset_type="draft_pick",
                    asset_id=asset_id,
                    asset_name=f"Draft Pick ({pick_info.get('year', '?')}, R{pick_info.get('round', '?')})",
                    metadata=pick_info
                ))
            else:
                # Regular player
                player_info = all_players_map.get(asset_id)
                player_name = None
                if player_info:
                    player_name = f"{player_info.first_name or ''} {player_info.last_name or ''}".strip()
                
                assets.append(TradeAsset(
                    asset_type="player",
                    asset_id=asset_id,
                    asset_name=player_name or f"Player {asset_id}",
                    metadata={"roster_id": roster_id}
                ))
    
    # Analyze drops (same logic but marked as going the other direction)
    if transaction.drops:
        for asset_id, roster_id in transaction.drops.items():
            if _is_draft_pick_identifier(asset_id):
                pick_info = _parse_draft_pick_identifier(asset_id)
                assets.append(TradeAsset(
                    asset_type="draft_pick",
                    asset_id=asset_id,
                    asset_name=f"Draft Pick ({pick_info.get('year', '?')}, R{pick_info.get('round', '?')})",
                    metadata={**pick_info, "direction": "dropped", "roster_id": roster_id}
                ))
            else:
                player_info = all_players_map.get(asset_id)
                player_name = None
                if player_info:
                    player_name = f"{player_info.first_name or ''} {player_info.last_name or ''}".strip()
                
                assets.append(TradeAsset(
                    asset_type="player",
                    asset_id=asset_id,
                    asset_name=player_name or f"Player {asset_id}",
                    metadata={"roster_id": roster_id, "direction": "dropped"}
                ))
    
    # Analyze traded picks if league_id is provided
    if league_id and transaction.roster_ids and len(transaction.roster_ids) >= 2:
        try:
            # Get all traded picks across all seasons in league history
            league_history_data = await client.get_league_history(league_id)
            league_history = [League(**item) for item in league_history_data] if league_history_data else []
            
            # Fetch traded picks from all seasons
            all_traded_picks = []
            for season_league in league_history:
                season_picks_data = await client.get_league_traded_picks(season_league.league_id)
                if season_picks_data:
                    all_traded_picks.extend([TradedPick(**pick) for pick in season_picks_data])
            
            if all_traded_picks:
                
                # Find picks that might have been involved in this trade based on timing
                transaction_timestamp = transaction.status_updated
                if transaction_timestamp:
                    # Look for picks where ownership change might coincide with this transaction
                    # This is an approximation since we don't have exact transaction IDs for pick trades
                    transaction_time = datetime.fromtimestamp(transaction_timestamp / 1000)
                    
                    for pick in all_traded_picks:
                        # Check if any of the rosters in this transaction were involved in pick ownership
                        if (pick.roster_id in transaction.roster_ids and 
                            pick.previous_owner_id and pick.previous_owner_id in transaction.roster_ids):
                            
                            # This pick was likely part of this trade
                            pick_name = f"{pick.season} Round {pick.round}"
                            direction = "to_" + str(pick.roster_id)
                            
                            assets.append(TradeAsset(
                                asset_type="traded_pick",
                                asset_id=f"{pick.season}_{pick.round}_{pick.roster_id}",
                                asset_name=pick_name,
                                metadata={
                                    "season": pick.season,
                                    "round": pick.round,
                                    "roster_id": pick.roster_id,
                                    "previous_owner_id": pick.previous_owner_id,
                                    "original_owner_id": pick.owner_id,
                                    "direction": direction
                                }
                            ))
        except Exception:
            # If traded picks analysis fails, continue with just player assets
            pass
    
    return assets


async def get_draft_pick_ownership_history(league_id: str, season: str) -> List[DraftPickOwnership]:
    """
    Get the ownership history for all draft picks in a league season.
    Tracks how draft picks moved between teams through trades.
    """
    # Get all draft picks for the season
    draft_picks = await get_league_draft_picks(league_id, season)
    
    # Get all transactions for the league across all years
    all_transactions = await get_all_league_transactions(league_id)
    
    # Get player data for name lookups
    all_players_data = await client.get_all_players()
    all_players_map = {p_id: Player(**p_data) for p_id, p_data in all_players_data.items()} if all_players_data else {}
    
    ownership_histories = []
    
    for pick in draft_picks:
        # Create draft pick identifier based on season and pick info
        pick_identifier = f"{season}_{pick.round}_{pick.pick_no:02d}"
        
        # Find all transactions that involved this draft pick
        ownership_changes = []
        original_owner_roster_id = pick.roster_id or pick.draft_slot  # Fallback to draft slot if roster_id not available
        final_owner_roster_id = original_owner_roster_id
        
        # Search through all transactions for this pick
        for transaction in all_transactions:
            if transaction.type == "trade":
                pick_involved = False
                transaction_roster_ids = []
                
                # Check if this pick was involved in the trade
                if transaction.adds:
                    for asset_id, receiving_roster_id in transaction.adds.items():
                        if _is_draft_pick_identifier(asset_id):
                            pick_info = _parse_draft_pick_identifier(asset_id)
                            # Match by year, round, and pick number
                            if (pick_info.get("year") == season and 
                                pick_info.get("round") == pick.round and
                                pick_info.get("pick_no") == pick.pick_no):
                                pick_involved = True
                                transaction_roster_ids.append(receiving_roster_id)
                                final_owner_roster_id = receiving_roster_id
                
                if transaction.drops:
                    for asset_id, giving_roster_id in transaction.drops.items():
                        if _is_draft_pick_identifier(asset_id):
                            pick_info = _parse_draft_pick_identifier(asset_id)
                            # Match by year, round, and pick number  
                            if (pick_info.get("year") == season and 
                                pick_info.get("round") == pick.round and
                                pick_info.get("pick_no") == pick.pick_no):
                                pick_involved = True
                                transaction_roster_ids.append(giving_roster_id)
                
                if pick_involved:
                    ownership_changes.append({
                        "transaction_id": transaction.transaction_id,
                        "timestamp": transaction.status_updated,
                        "roster_ids_involved": transaction_roster_ids,
                        "type": "trade"
                    })
        
        # Determine selected player info
        selected_player_name = None
        if pick.player_id and pick.player_id in all_players_map:
            player = all_players_map[pick.player_id]
            selected_player_name = f"{player.first_name or ''} {player.last_name or ''}".strip()
        
        ownership_history = DraftPickOwnership(
            draft_id=pick.draft_id,
            pick_no=pick.pick_no,
            round=pick.round,
            original_owner_roster_id=original_owner_roster_id,
            final_owner_roster_id=final_owner_roster_id,
            ownership_changes=ownership_changes,
            selected_player_id=pick.player_id,
            selected_player_name=selected_player_name
        )
        
        ownership_histories.append(ownership_history)
    
    return ownership_histories


async def get_draft_pick_journey(league_id: str, season: str, pick_no: int) -> Dict[str, Any]:
    """
    Get the complete journey of a specific draft pick, including performance analysis
    of the player drafted with that pick.
    """
    # Get the specific draft pick
    draft_picks = await get_league_draft_picks(league_id, season)
    target_pick = next((pick for pick in draft_picks if pick.pick_no == pick_no), None)
    
    if not target_pick:
        return {"error": f"Draft pick #{pick_no} not found for season {season}"}
    
    # Get ownership history for this specific pick
    ownership_histories = await get_draft_pick_ownership_history(league_id, season)
    pick_ownership = next((hist for hist in ownership_histories if hist.pick_no == pick_no), None)
    
    # Get player performance data if a player was selected
    player_performance = None
    if target_pick.player_id:
        try:
            # Get player stint performance in this league
            player_stints = await get_player_stints_with_performance(league_id, target_pick.player_id)
            
            # Get aggregated career stats across all seasons
            league_history_data = await client.get_league_history(league_id)
            league_history = [League(**item) for item in league_history_data] if league_history_data else []
            seasons = list(set(league.season for league in league_history if league.season))
            
            career_stats = {}
            for season_year in seasons:
                season_stats = await get_player_aggregated_stats(target_pick.player_id, season_year)
                career_stats[season_year] = season_stats
            
            player_performance = {
                "stints": player_stints,
                "career_stats_by_season": career_stats
            }
        except Exception as e:
            player_performance = {"error": f"Failed to fetch player performance: {str(e)}"}
    
    # Get roster information for context
    league_rosters_data = await client.get_league_rosters(league_id)
    roster_lookup = {}
    if league_rosters_data:
        for roster_data in league_rosters_data:
            try:
                roster = Roster(**roster_data)
                roster_lookup[roster.roster_id] = {
                    "roster_id": roster.roster_id,
                    "owner_id": roster.owner_id,
                    "team_name": (roster.metadata or {}).get("team_name", "Unknown Team")
                }
            except Exception:
                continue
    
    # Get user info for current owner
    current_owner_info = None
    if pick_ownership and pick_ownership.final_owner_roster_id in roster_lookup:
        roster_info = roster_lookup[pick_ownership.final_owner_roster_id]
        if roster_info["owner_id"]:
            user_data = await client.get_user_by_user_id(roster_info["owner_id"])
            if user_data:
                current_owner_info = {
                    "roster_id": roster_info["roster_id"],
                    "team_name": roster_info["team_name"],
                    "username": user_data.get("username"),
                    "display_name": user_data.get("display_name")
                }
    
    return {
        "draft_pick_info": target_pick,
        "ownership_history": pick_ownership,
        "current_owner": current_owner_info,
        "player_performance": player_performance,
        "draft_context": {
            "season": season,
            "round": target_pick.round,
            "pick_in_round": pick_no - ((target_pick.round - 1) * len(roster_lookup)) if roster_lookup else pick_no,
            "total_picks_analyzed": len(draft_picks)
        }
    }


async def find_connected_trades(league_id: str, time_window_hours: int = 24) -> List[TradeTree]:
    """
    Find connected trade relationships within a league.
    Trades are considered connected if they involve the same assets within a time window.
    """
    # Get all transactions
    all_transactions = await get_all_league_transactions(league_id)
    
    # Filter only trade transactions
    trade_transactions = [tx for tx in all_transactions if tx.type == "trade"]
    
    # Sort by timestamp
    trade_transactions.sort(key=lambda x: x.status_updated or 0)
    
    # Get player data for asset analysis
    all_players_data = await client.get_all_players()
    all_players_map = {p_id: Player(**p_data) for p_id, p_data in all_players_data.items()} if all_players_data else {}
    
    # Build trade nodes with asset information
    trade_nodes = []
    for transaction in trade_transactions:
        assets = await analyze_trade_assets(transaction, all_players_map, league_id)
        
        trade_node = TradeNode(
            transaction_id=transaction.transaction_id,
            timestamp=transaction.status_updated,
            date=datetime.fromtimestamp(transaction.status_updated / 1000).strftime("%Y-%m-%d %H:%M:%S") if transaction.status_updated else None,
            roster_ids=transaction.roster_ids or [],
            assets_exchanged=assets
        )
        trade_nodes.append(trade_node)
    
    # Find connected trades based on asset overlap and time proximity
    trade_trees = []
    processed_trades = set()
    
    for i, root_trade in enumerate(trade_nodes):
        if root_trade.transaction_id in processed_trades:
            continue
        
        # Start a new trade tree
        connected_trades = [root_trade]
        processed_trades.add(root_trade.transaction_id)
        
        # Find trades connected to this one
        root_assets = set(asset.asset_id for asset in root_trade.assets_exchanged)
        root_timestamp = root_trade.timestamp or 0
        
        # Check subsequent trades for connections
        for j, candidate_trade in enumerate(trade_nodes[i+1:], i+1):
            if candidate_trade.transaction_id in processed_trades:
                continue
            
            candidate_assets = set(asset.asset_id for asset in candidate_trade.assets_exchanged)
            candidate_timestamp = candidate_trade.timestamp or 0
            
            # Check for asset overlap
            asset_overlap = root_assets.intersection(candidate_assets)
            
            # Check time proximity (within specified hours)
            time_diff_hours = abs(candidate_timestamp - root_timestamp) / (1000 * 60 * 60)
            
            if asset_overlap and time_diff_hours <= time_window_hours:
                # This trade is connected
                connected_trades.append(candidate_trade)
                processed_trades.add(candidate_trade.transaction_id)
                
                # Update the root trade's connected trades list
                root_trade.connected_trades.append(candidate_trade.transaction_id)
                candidate_trade.connected_trades.append(root_trade.transaction_id)
                
                # Expand asset set for future matching
                root_assets.update(candidate_assets)
        
        # Create a trade tree if there are assets involved (be more inclusive)
        if len(root_assets) > 0:
            # Calculate timespan
            timestamps = [trade.timestamp for trade in connected_trades if trade.timestamp]
            timespan_days = None
            if len(timestamps) > 1:
                timespan_days = int((max(timestamps) - min(timestamps)) / (1000 * 60 * 60 * 24))
            
            # Get unique leagues involved
            leagues_involved = list(set([league_id]))  # For now, single league
            
            trade_tree = TradeTree(
                root_transaction_id=root_trade.transaction_id,
                all_transactions=connected_trades,
                total_assets_involved=len(root_assets),
                leagues_involved=leagues_involved,
                timespan_days=timespan_days
            )
            trade_trees.append(trade_tree)
    
    return trade_trees


async def analyze_trade_chain_impact(league_id: str, transaction_id: str) -> Dict[str, Any]:
    """
    Analyze the impact of a trade chain starting from a specific transaction.
    Shows how assets flow through multiple connected trades.
    """
    # Find all trade trees
    trade_trees = await find_connected_trades(league_id)
    
    # Find the trade tree containing this transaction
    target_tree = None
    for tree in trade_trees:
        if tree.root_transaction_id == transaction_id or any(
            trade.transaction_id == transaction_id for trade in tree.all_transactions
        ):
            target_tree = tree
            break
    
    if not target_tree:
        return {"error": f"Transaction {transaction_id} not found in any trade tree"}
    
    # Analyze asset flow through the chain
    asset_flow = {}
    roster_impact = {}
    
    for trade in target_tree.all_transactions:
        for asset in trade.assets_exchanged:
            asset_id = asset.asset_id
            if asset_id not in asset_flow:
                asset_flow[asset_id] = {
                    "asset_info": asset,
                    "trade_history": []
                }
            
            asset_flow[asset_id]["trade_history"].append({
                "transaction_id": trade.transaction_id,
                "timestamp": trade.timestamp,
                "date": trade.date
            })
        
        # Track roster involvement
        for roster_id in trade.roster_ids:
            if roster_id not in roster_impact:
                roster_impact[roster_id] = {
                    "trades_involved": 0,
                    "assets_gained": [],
                    "assets_lost": []
                }
            roster_impact[roster_id]["trades_involved"] += 1
    
    # Calculate net gains/losses per roster
    for trade in target_tree.all_transactions:
        # This is simplified - in reality we'd need to parse adds/drops more carefully
        for asset in trade.assets_exchanged:
            metadata = asset.metadata or {}
            roster_id = metadata.get("roster_id")
            direction = metadata.get("direction", "added")
            
            if roster_id and roster_id in roster_impact:
                if direction == "dropped":
                    roster_impact[roster_id]["assets_lost"].append(asset)
                else:
                    roster_impact[roster_id]["assets_gained"].append(asset)
    
    return {
        "trade_tree": target_tree,
        "asset_flow": asset_flow,
        "roster_impact": roster_impact,
        "chain_summary": {
            "total_trades": len(target_tree.all_transactions),
            "total_assets": target_tree.total_assets_involved,
            "timespan_days": target_tree.timespan_days,
            "start_date": min([t.date for t in target_tree.all_transactions if t.date], default=None),
            "end_date": max([t.date for t in target_tree.all_transactions if t.date], default=None)
        }
    }


async def get_historical_data_coverage(league_id: str) -> Dict[str, Any]:
    """
    Validate historical data coverage for a league.
    Shows which seasons have data available and transaction counts.
    """
    # Get league history
    league_history_data = await client.get_league_history(league_id)
    league_history = [League(**item) for item in league_history_data] if league_history_data else []
    
    if not league_history:
        return {"error": f"No league history found for league {league_id}"}
    
    coverage_info = []
    total_transactions = 0
    
    # Check each season
    for season_league in league_history:
        try:
            # Get transactions for this season
            season_transactions = await get_single_season_transactions(season_league.league_id)
            transaction_count = len(season_transactions)
            total_transactions += transaction_count
            
            # Get draft information if available
            drafts_data = await client.get_league_drafts(season_league.league_id)
            drafts_count = len(drafts_data) if drafts_data else 0
            
            coverage_info.append({
                "season": season_league.season,
                "league_id": season_league.league_id,
                "league_name": season_league.name,
                "transactions_count": transaction_count,
                "drafts_count": drafts_count,
                "status": season_league.status,
                "has_data": transaction_count > 0 or drafts_count > 0
            })
        except Exception as e:
            coverage_info.append({
                "season": season_league.season,
                "league_id": season_league.league_id,
                "league_name": season_league.name,
                "transactions_count": 0,
                "drafts_count": 0,
                "status": "error",
                "has_data": False,
                "error": str(e)
            })
    
    # Sort by season (newest first)
    coverage_info.sort(key=lambda x: x["season"], reverse=True)
    
    return {
        "total_seasons": len(coverage_info),
        "total_transactions": total_transactions,
        "seasons_with_data": len([s for s in coverage_info if s["has_data"]]),
        "coverage_by_season": coverage_info
    }