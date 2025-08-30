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


class Transaction(BaseModel):
    transaction_id: str
    league_id: str
    type: str
    status: str
    status_updated: Optional[int] = None  # Unix timestamp in ms
    adds: Optional[Dict[str, Any]] = None
    drops: Optional[Dict[str, Any]] = None
    roster_ids: Optional[List[int]] = None
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
