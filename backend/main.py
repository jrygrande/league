from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any

from . import database
from .services import sleeper_service
from .models.sleeper import User, League, Roster, Draft, Player, Stats, Transaction, Matchup, PlayerStint, DraftPickInfo, DraftPickOwnership, TradeAsset, TradeNode, TradeTree, PickChain, PickIdentity, TradeGroup, CompleteAssetTree, TradeGraph, GraphBasedAssetGenealogy


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.create_tables()
    yield


app = FastAPI(lifespan=lifespan)

# Configure CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js development server
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    if transactions_data:
        for tx in transactions_data:
            tx["league_id"] = league_id
            # Convert draft_picks to DraftPickMovement objects
            if "draft_picks" in tx and tx["draft_picks"]:
                from .models.sleeper import DraftPickMovement
                draft_pick_movements = []
                for pick_data in tx["draft_picks"]:
                    if isinstance(pick_data, dict):
                        draft_pick_movements.append(DraftPickMovement(**pick_data))
                tx["draft_picks"] = draft_pick_movements
    return [Transaction(**tx) for tx in transactions_data] if transactions_data else []


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


@app.get("/draft/{draft_id}/picks")
async def get_draft_picks(draft_id: str):
    picks_data = await sleeper_service.client.get_draft_picks(draft_id)
    return picks_data


@app.get("/league/{league_id}/draft_picks/{season}", response_model=List[DraftPickInfo])
async def get_league_draft_picks(league_id: str, season: str):
    """Get all draft picks for a specific league and season."""
    return await sleeper_service.get_league_draft_picks(league_id, season)


@app.get("/analysis/league/{league_id}/trade/{transaction_id}/assets", response_model=List[TradeAsset])
async def analyze_trade_assets_endpoint(league_id: str, transaction_id: str):
    """Analyze what assets (players and picks) were involved in a specific trade."""
    # Get the specific transaction
    all_transactions = await sleeper_service.get_all_league_transactions(league_id)
    target_transaction = next((tx for tx in all_transactions if tx.transaction_id == transaction_id), None)
    
    if not target_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Get player data for name lookups
    all_players_data = await sleeper_service.client.get_all_players()
    all_players_map = {p_id: Player(**p_data) for p_id, p_data in all_players_data.items()} if all_players_data else {}
    
    return await sleeper_service.analyze_trade_assets(target_transaction, all_players_map, league_id)


@app.get("/league/{league_id}/draft_picks/{season}/ownership", response_model=List[DraftPickOwnership])
async def get_draft_pick_ownership_history(league_id: str, season: str):
    """Get the ownership history for all draft picks in a league season, including trade history."""
    return await sleeper_service.get_draft_pick_ownership_history(league_id, season)


@app.get("/league/{league_id}/draft_picks/{season}/{pick_no}/journey")
async def get_draft_pick_journey(league_id: str, season: str, pick_no: int):
    """Get the complete journey of a specific draft pick with performance analysis."""
    return await sleeper_service.get_draft_pick_journey(league_id, season, pick_no)


@app.get("/league/{league_id}/trade_trees", response_model=List[TradeTree])
async def get_connected_trades(league_id: str, time_window_hours: int = 24):
    """Find connected trade relationships within a league."""
    return await sleeper_service.find_connected_trades(league_id, time_window_hours)


@app.get("/analysis/league/{league_id}/trade_chain/{transaction_id}")
async def analyze_trade_chain_impact(league_id: str, transaction_id: str):
    """Analyze the impact of a trade chain starting from a specific transaction."""
    return await sleeper_service.analyze_trade_chain_impact(league_id, transaction_id)


@app.get("/league/{league_id}/historical_coverage")
async def get_historical_data_coverage(league_id: str):
    """Validate historical data coverage for a league."""
    return await sleeper_service.get_historical_data_coverage(league_id)


@app.get("/analysis/pick_chain/{league_id}/{season}/{round}/{original_owner}", response_model=PickChain)
async def trace_pick_ownership_chain(league_id: str, season: str, round: int, original_owner: int):
    """Trace the complete ownership chain of a specific pick through all trades."""
    return await sleeper_service.trace_pick_ownership_chain(league_id, season, round, original_owner)


@app.get("/analysis/league/{league_id}/pick_identities", response_model=List[PickIdentity])
async def get_league_pick_identities(league_id: str):
    """Get unique identities for all draft picks in league history to track them through trades."""
    return await sleeper_service.create_pick_identities(league_id)


@app.get("/analysis/league/{league_id}/trade_groups", response_model=List[TradeGroup])
async def get_league_trade_groups(league_id: str, time_window_days: int = 7):
    """Group related trades together based on timing, participants, and asset relationships."""
    return await sleeper_service.find_trade_groups(league_id, time_window_days)


@app.get("/analysis/league/{league_id}/asset_tree/{root_asset_id}", response_model=CompleteAssetTree)
async def get_complete_asset_tree(league_id: str, root_asset_id: str):
    """Build complete asset genealogy tree starting from a root asset (like Travis Kelce)."""
    return await sleeper_service.build_complete_asset_tree(league_id, root_asset_id)


@app.get("/analysis/league/{league_id}/complete_trade_graph", response_model=TradeGraph)
async def get_complete_trade_graph(league_id: str):
    """Build comprehensive trade graph from all historical transactions."""
    return await sleeper_service.build_complete_trade_graph(league_id)


@app.get("/analysis/league/{league_id}/asset_genealogy/{root_asset_id}", response_model=GraphBasedAssetGenealogy)
async def get_graph_based_asset_genealogy(league_id: str, root_asset_id: str):
    """Get true multi-hop asset genealogy using complete trade graph analysis."""
    return await sleeper_service.trace_asset_genealogy_from_graph(league_id, root_asset_id)


@app.get("/analysis/league/{league_id}/manager/{roster_id}/asset_trace/{asset_id}")
async def trace_asset_for_manager(league_id: str, roster_id: int, asset_id: str):
    """Trace how a manager acquired an asset and what it became through all subsequent trades.
    
    Returns:
    - How the asset was acquired (draft, trade chain, etc.)
    - All subsequent trades and transformations
    - Current status/outcome of the asset
    """
    return await sleeper_service.trace_manager_asset_lifecycle(league_id, roster_id, asset_id)


@app.get("/analysis/league/{league_id}/manager/{roster_id}/comprehensive_chain/{asset_id}")
async def get_comprehensive_asset_chain(league_id: str, roster_id: int, asset_id: str):
    """Get complete multi-generation asset chain showing how an asset was acquired,
    what was received when trading it away, and what all those assets became.
    
    Perfect for tracing complex trades like Kelce → multiple picks → final players.
    """
    return await sleeper_service.trace_comprehensive_asset_chain(league_id, roster_id, asset_id)