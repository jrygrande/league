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
                tx_data["league_id"] = league_id
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