from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel


class User(BaseModel):
    user_id: str
    username: str
    display_name: Optional[str] = None
    avatar: Optional[str] = None


class League(BaseModel):
    league_id: str
    name: str
    season: str
    total_rosters: int
    status: str
    previous_league_id: Optional[str] = None
    settings: Dict[str, Any]
    scoring_settings: Dict[str, Any]
    roster_positions: List[str]


class Roster(BaseModel):
    roster_id: int
    league_id: str
    owner_id: Optional[str] = None
    players: Optional[List[str]] = None
    starters: Optional[List[str]] = None
    reserve: Optional[List[str]] = None
    settings: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class Draft(BaseModel):
    draft_id: str
    league_id: str
    status: str
    type: str
    season: str
    settings: Dict[str, Any]
    metadata: Dict[str, Any]


class Pick(BaseModel):
    player_id: Optional[str] = None
    pick_no: int
    round: int
    roster_id: Optional[int] = None
    draft_id: str
    metadata: Dict[str, Any]


class Player(BaseModel):
    player_id: str
    full_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    position: Optional[str] = None
    team: Optional[str] = None
    age: Optional[int] = None
    # Add other common player fields as needed


class Stats(BaseModel):
    player_id: str
    week: int
    season: str
    pts_ppr: Optional[float] = None
    gp: Optional[int] = None
    # Add other relevant stats fields


class DraftPickMovement(BaseModel):
    season: str
    round: int
    roster_id: int  # ORIGINAL owner of the pick (who initially had this draft slot)
    owner_id: int   # NEW owner after this trade (who's receiving the pick)
    previous_owner_id: int  # Roster TRADING AWAY the pick in this transaction
    league_id: Optional[str] = None


class Transaction(BaseModel):
    transaction_id: str
    league_id: str
    type: str
    status: str
    status_updated: Optional[int] = None  # Unix timestamp in ms
    adds: Optional[Dict[str, Any]] = None
    drops: Optional[Dict[str, Any]] = None
    roster_ids: Optional[List[int]] = None
    draft_picks: Optional[List[DraftPickMovement]] = None
    metadata: Optional[Dict[str, Any]] = None


class Matchup(BaseModel):
    matchup_id: Optional[int] = None
    league_id: str
    week: int
    roster_id: int
    points: float
    players: List[str]
    starters: List[str]
    # Add other relevant matchup fields


class PlayerStint(BaseModel):
    start_date: datetime
    end_date: Optional[datetime] = None
    team_name: str
    owner_username: str
    owner_display_name: str
    aggregated_stats: Dict[str, Any]


class DraftPickInfo(BaseModel):
    draft_id: str
    pick_no: int
    round: int
    draft_slot: Optional[int] = None
    player_id: Optional[str] = None
    roster_id: Optional[int] = None
    picked_by: Optional[str] = None
    is_keeper: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class DraftPickOwnership(BaseModel):
    draft_id: str
    pick_no: int
    round: int
    original_owner_roster_id: int
    final_owner_roster_id: int
    ownership_changes: List[Dict[str, Any]]  # List of trades that moved this pick
    selected_player_id: Optional[str] = None
    selected_player_name: Optional[str] = None


class TradeAsset(BaseModel):
    asset_type: str  # "player", "draft_pick", "faab"
    asset_id: str    # player_id or pick identifier
    asset_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TradeNode(BaseModel):
    transaction_id: str
    timestamp: Optional[int] = None
    date: Optional[str] = None
    roster_ids: List[int]
    assets_exchanged: List[TradeAsset]
    connected_trades: List[str] = []  # List of transaction_ids of connected trades


class TradeTree(BaseModel):
    root_transaction_id: str
    all_transactions: List[TradeNode]
    total_assets_involved: int
    leagues_involved: List[str]
    timespan_days: Optional[int] = None


class TradedPick(BaseModel):
    season: str
    round: int
    roster_id: int  # Current owner
    owner_id: int   # Original owner  
    previous_owner_id: Optional[int] = None


class PickOwnershipStep(BaseModel):
    owner_roster_id: int
    previous_owner_roster_id: Optional[int] = None
    step_number: int  # 1, 2, 3, etc. in the chain
    trade_context: Optional[Dict[str, Any]] = None  # Associated trade info if known


class PickChain(BaseModel):
    season: str
    round: int
    original_owner: int
    ownership_history: List[PickOwnershipStep]
    final_owner: int
    draft_outcome: Optional[Dict[str, Any]] = None  # Player drafted or None if not used


class AssetGenealogy(BaseModel):
    root_asset_id: str  # Original draft pick or player
    root_asset_name: str
    root_asset_type: str  # "draft_pick", "player"
    trade_branches: List[Dict[str, Any]]  # Each major trade and its consequences
    final_outcomes: List[Dict[str, Any]]  # Current state of all descendant assets


class TradeStep(BaseModel):
    transaction_id: str
    timestamp: Optional[int] = None
    from_roster_id: int
    to_roster_id: int
    trade_context: Optional[Dict[str, Any]] = None


class PickIdentity(BaseModel):
    season: str
    round: int
    original_roster_id: int  # Who originally owned this pick
    pick_uuid: str  # Unique ID: f"{season}_{round}_{original_roster_id}"
    current_owner: int
    trade_history: List[TradeStep]  # Every trade that moved this pick
    final_outcome: Optional[Dict[str, Any]] = None  # Who was drafted


class AssetExchange(BaseModel):
    transaction_id: str
    timestamp: Optional[int] = None
    date: Optional[str] = None
    assets_out: List[TradeAsset]  # What was given up
    assets_in: List[TradeAsset]   # What was received
    net_value_change: Optional[Dict[str, Any]] = None  # Draft capital, player value, etc.


class TradeGroup(BaseModel):
    primary_transaction_id: str  # The "root" trade (e.g., Kelce trade)
    related_transaction_ids: List[str]  # Subsequent connected trades
    time_window_days: Optional[int] = None  # How long the deal sequence took
    participants: List[int]  # All roster IDs involved across trades
    asset_flow_summary: Optional[Dict[str, Any]] = None  # Net asset movement
    trade_sequence: List[AssetExchange]  # Chronological sequence of exchanges


class CompleteAssetTree(BaseModel):
    root_asset: str
    root_asset_metadata: Optional[Dict[str, Any]] = None
    trade_sequence: List[AssetExchange]
    final_descendants: List[Dict[str, Any]]
    tree_depth: int  # Number of trade hops from root to final assets
    total_assets_involved: int


class AssetNode(BaseModel):
    """Represents a single asset (player or pick) in the trade graph."""
    asset_id: str
    asset_type: str  # "player", "draft_pick"
    asset_name: Optional[str] = None
    current_owner: Optional[int] = None
    original_owner: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class TradeEdge(BaseModel):
    """Represents a single asset movement between rosters in a trade."""
    transaction_id: str
    timestamp: Optional[int] = None
    from_roster_id: int
    to_roster_id: int
    asset_id: str
    trade_context: Optional[Dict[str, Any]] = None


class TradeGraph(BaseModel):
    """Complete trade network for a league."""
    league_id: str
    nodes: Dict[str, AssetNode]  # asset_id -> AssetNode
    edges: List[TradeEdge]  # All asset movements
    transactions: Dict[str, Dict[str, Any]]  # transaction_id -> transaction details
    roster_names: Dict[int, str]  # roster_id -> team/owner name
    timeline: List[str]  # chronologically ordered transaction_ids


class AssetPath(BaseModel):
    """Represents a path through the trade graph from one asset to another."""
    from_asset_id: str
    to_asset_id: str
    path_edges: List[TradeEdge]
    path_length: int
    time_span_days: Optional[int] = None
    participants: List[int]  # all roster_ids involved in the path


class GraphBasedAssetGenealogy(BaseModel):
    """Complete asset genealogy built from trade graph traversal."""
    root_asset_id: str
    root_asset_info: AssetNode
    descendant_paths: List[AssetPath]
    final_assets: List[AssetNode]
    trade_network_stats: Dict[str, Any]
    generation_depth: int  # max path length from root to any descendant


class TradeStep(BaseModel):
    """Represents a single step in a trade chain."""
    transaction_id: str
    timestamp: Optional[int] = None
    date: Optional[str] = None
    from_roster_id: int
    from_manager: str
    to_roster_id: int
    to_manager: str
    trade_context: Optional[Dict[str, Any]] = None


class AssetAcquisition(BaseModel):
    """How an asset was originally acquired by a manager."""
    acquisition_type: str  # "draft", "trade", "waiver", "free_agent"
    acquisition_date: Optional[str] = None
    acquisition_details: Dict[str, Any]
    trade_chain: Optional[List[TradeStep]] = None  # If acquired via trade


class AssetDisposal(BaseModel):
    """How an asset was disposed of by a manager."""
    disposal_type: str  # "trade", "drop", "still_owned"
    disposal_date: Optional[str] = None
    disposal_details: Dict[str, Any]
    subsequent_transformations: List[Dict[str, Any]] = []  # What it became after leaving


class ManagerAssetTrace(BaseModel):
    """Complete lifecycle trace of an asset for a specific manager."""
    asset_id: str
    asset_name: str
    asset_type: str  # "player", "draft_pick"
    manager_roster_id: int
    manager_name: str
    
    # How they got it
    acquisition: AssetAcquisition
    
    # What they did with it
    disposal: AssetDisposal
    
    # Timeline summary
    ownership_period: Dict[str, Any]  # start_date, end_date, duration_days
    
    # Asset transformations (if it was a pick that became a player, etc.)
    transformations: List[Dict[str, Any]] = []


class AssetChainBranch(BaseModel):
    """Represents one branch of what an asset became through trades."""
    initial_asset: Dict[str, Any]  # What asset started this branch
    
    # What was traded away (the initial asset + any packaged assets)
    trade_package: List[Dict[str, Any]] = []  # Full package given away
    
    # What was received in return for the package
    assets_received_in_trade: List[Dict[str, Any]] = []  # Compensation received
    
    # Trade details
    trade_details: Optional[Dict[str, Any]] = None  # Transaction info
    
    # Subsequent chains for each received asset
    sub_branches: List["AssetChainBranch"] = []  # Recursive branches
    
    # Final outcomes of all assets in this branch
    final_outcomes: List[Dict[str, Any]] = []  # What everything became
    
    # Branch metrics
    total_depth: int = 0  # Max depth of sub-branches
    total_assets_generated: int = 0  # Total assets created from this branch


class ComprehensiveAssetChain(BaseModel):
    """Complete multi-generation asset chain showing full acquisition and disposal tree."""
    asset_id: str
    asset_name: str
    asset_type: str
    manager_roster_id: int
    manager_name: str
    
    # Original acquisition - how the manager originally got this asset
    original_acquisition: Dict[str, Any]  # Draft pick used, trade, etc.
    
    # When traded away, what was received in return
    trade_away_details: Optional[Dict[str, Any]] = None
    assets_received: List[Dict[str, Any]] = []
    
    # What each received asset became through subsequent trades
    asset_branches: List[AssetChainBranch] = []
    
    # Summary statistics
    chain_summary: Dict[str, Any]  # Total value generated, final outcomes count, etc.
