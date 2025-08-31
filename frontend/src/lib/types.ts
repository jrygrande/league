// Core API Response Types
export interface User {
  user_id: string
  username: string
  display_name?: string
  avatar?: string
}

export interface League {
  league_id: string
  name: string
  season: string
  total_rosters: number
  status: string
  previous_league_id?: string
  settings: Record<string, any>
  scoring_settings: Record<string, any>
  roster_positions: string[]
}

export interface Player {
  player_id: string
  full_name?: string
  first_name?: string
  last_name?: string
  position?: string
  team?: string
  age?: number
}

export interface DraftPickMovement {
  season: string
  round: number
  roster_id: number
  owner_id: number
  previous_owner_id: number
  league_id?: string
}

export interface Roster {
  roster_id: number
  league_id: string
  owner_id?: string
  players?: string[]
  starters?: string[]
  reserve?: string[]
  settings?: Record<string, any>
  metadata?: Record<string, any>
}

export interface Transaction {
  transaction_id: string
  league_id: string
  type: string
  status: string
  status_updated?: number
  adds?: Record<string, any>
  drops?: Record<string, any>
  roster_ids?: number[]
  draft_picks?: DraftPickMovement[]
  metadata?: Record<string, any>
}

// Asset Chain Types
export interface AssetChainBranch {
  initial_asset: Record<string, any>
  trade_package: Record<string, any>[]
  assets_received_in_trade: Record<string, any>[]
  trade_details?: Record<string, any>
  sub_branches: AssetChainBranch[]
  final_outcomes: Record<string, any>[]
  branch_summary: Record<string, any>
}

export interface ComprehensiveAssetChain {
  asset_id: string
  asset_name: string
  asset_type: string
  manager_roster_id: number
  manager_name: string
  original_acquisition: Record<string, any>
  trade_away_details?: Record<string, any>
  assets_received: Record<string, any>[]
  asset_branches: AssetChainBranch[]
  chain_summary: Record<string, any>
}

// UI State Types
export interface PlayerSearchResult extends Player {
  // Additional UI fields if needed
}

export interface LeagueSelectOption {
  value: string
  label: string
  league: League
}

export interface UserFormData {
  username: string
}

export interface LeagueFormData {
  leagueId: string
}

export interface PlayerSearchFormData {
  query: string
  selectedPlayer?: Player
}

// Error Types
export interface ApiError {
  message: string
  status?: number
  code?: string
}

// Query Keys for React Query
export const QUERY_KEYS = {
  user: (username: string) => ['user', username] as const,
  userLeagues: (username: string, season: string) => ['user', username, 'leagues', season] as const,
  leagueRosters: (leagueId: string) => ['league', leagueId, 'rosters'] as const,
  players: () => ['players'] as const,
  playerSearch: (query: string) => ['players', 'search', query] as const,
  assetChain: (leagueId: string, rosterId: number, assetId: string) => 
    ['assetChain', leagueId, rosterId, assetId] as const,
} as const