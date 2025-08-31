import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'
import { QUERY_KEYS } from '@/lib/types'

export function useLeagueRosters(leagueId: string) {
  return useQuery({
    queryKey: QUERY_KEYS.leagueRosters(leagueId),
    queryFn: () => apiClient.getLeagueRosters(leagueId),
    enabled: !!leagueId,
    retry: (failureCount, error: any) => {
      // Don't retry if league not found
      if (error?.response?.status === 404) {
        return false
      }
      return failureCount < 3
    },
    // Roster data doesn't change frequently during the season
    staleTime: 1000 * 60 * 5, // 5 minutes
  })
}