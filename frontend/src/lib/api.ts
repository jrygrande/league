import axios, { AxiosInstance } from 'axios'
import { User, League, Player, Roster, ComprehensiveAssetChain, AllUserLeaguesResponse, LeagueHistory } from './types'

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`)
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => {
        return response
      },
      (error) => {
        console.error('API Error:', error.response?.data || error.message)
        
        // Let 404s be handled by individual endpoints or hooks
        // Don't automatically convert them to null responses
        
        return Promise.reject(error)
      }
    )
  }

  // User endpoints
  async getUserByUsername(username: string): Promise<User | null> {
    try {
      const response = await this.client.get(`/user/${username}`)
      return response.data
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null
      }
      throw error
    }
  }

  async getUserLeagues(username: string, season: string): Promise<League[]> {
    const response = await this.client.get(`/user/${username}/leagues/${season}`)
    return response.data || []
  }

  async getAllUserLeagues(username: string): Promise<AllUserLeaguesResponse> {
    const response = await this.client.get(`/user/${username}/all-leagues`)
    return response.data
  }

  // League endpoints
  async getLeagueRosters(leagueId: string): Promise<Roster[]> {
    const response = await this.client.get(`/league/${leagueId}/rosters`)
    return response.data || []
  }

  async getLeagueHistory(leagueId: string): Promise<LeagueHistory> {
    const response = await this.client.get(`/league/${leagueId}/full-history`)
    return response.data
  }

  // Player endpoints
  async getAllPlayers(): Promise<Record<string, Player>> {
    const response = await this.client.get('/players')
    return response.data || {}
  }

  async searchPlayers(query: string): Promise<Player[]> {
    // For now, we'll get all players and filter client-side
    // In the future, we could add a server-side search endpoint
    const allPlayers = await this.getAllPlayers()
    const players = Object.values(allPlayers)
    
    if (!query || query.length < 2) {
      return []
    }
    
    const searchTerm = query.toLowerCase()
    return players
      .filter(player => 
        player.full_name?.toLowerCase().includes(searchTerm) ||
        player.first_name?.toLowerCase().includes(searchTerm) ||
        player.last_name?.toLowerCase().includes(searchTerm)
      )
      .slice(0, 10) // Limit to 10 results
  }

  // Asset chain endpoints
  async getComprehensiveAssetChain(
    leagueId: string, 
    rosterId: number, 
    assetId: string
  ): Promise<ComprehensiveAssetChain | null> {
    const response = await this.client.get(
      `/analysis/league/${leagueId}/manager/${rosterId}/comprehensive_chain/${assetId}`
    )
    return response.data
  }
}

export const apiClient = new ApiClient()
export default apiClient