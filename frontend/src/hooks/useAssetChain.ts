import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'
import { QUERY_KEYS } from '@/lib/types'

export function useAssetChain(leagueId: string, rosterId: number, assetId: string) {
  return useQuery({
    queryKey: QUERY_KEYS.assetChain(leagueId, rosterId, assetId),
    queryFn: () => apiClient.getComprehensiveAssetChain(leagueId, rosterId, assetId),
    enabled: !!leagueId && !!rosterId && !!assetId,
    retry: (failureCount, error: any) => {
      // Don't retry if asset chain not found
      if (error?.response?.status === 404) {
        return false
      }
      return failureCount < 3
    },
    // This data is less likely to change frequently
    staleTime: 1000 * 60 * 10, // 10 minutes
  })
}