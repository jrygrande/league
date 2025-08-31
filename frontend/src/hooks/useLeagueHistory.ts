import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'
import { QUERY_KEYS } from '@/lib/types'

export function useLeagueHistory(leagueId: string) {
  return useQuery({
    queryKey: QUERY_KEYS.leagueHistory(leagueId),
    queryFn: () => apiClient.getLeagueHistory(leagueId),
    enabled: !!leagueId,
    retry: (failureCount, error: any) => {
      // Don't retry if league not found
      if (error?.response?.status === 404) {
        return false
      }
      return failureCount < 3
    },
    // League history changes very infrequently
    staleTime: 1000 * 60 * 30, // 30 minutes
  })
}