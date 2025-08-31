// TypeScript test to verify our interfaces match API responses
import { User, Player, League } from './src/lib/types'

// Test sample data structures
const testUser: User = {
  user_id: "199067175669993472",
  username: "testuser",
  display_name: "testuser",
  avatar: "bc6df80fa76e459b904633018fbc9a33"
}

const testPlayer: Player = {
  player_id: "6462",
  full_name: "Ellis Richardson",
  first_name: "Ellis",
  last_name: "Richardson",
  position: "TE",
  team: undefined,
  age: 26
}

const testLeague: League = {
  league_id: "test123",
  name: "Test League",
  season: "2024",
  total_rosters: 12,
  status: "complete",
  previous_league_id: undefined,
  settings: {},
  scoring_settings: {},
  roster_positions: ["QB", "RB", "WR", "TE"]
}

// These should all compile without errors if our types are correct
console.log('TypeScript interface test:', {
  userValid: !!testUser.user_id,
  playerValid: !!testPlayer.player_id,
  leagueValid: !!testLeague.league_id
})

export { testUser, testPlayer, testLeague }