from typing import List, Dict, Any, Optional
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
    metadata: Dict[str, Any]


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
