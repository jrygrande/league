import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'
import { QUERY_KEYS } from '@/lib/types'

export function useUserLeagues(username: string, season: string) {
  return useQuery({
    queryKey: QUERY_KEYS.userLeagues(username, season),
    queryFn: () => apiClient.getUserLeagues(username, season),
    enabled: !!username && !!season,
    retry: (failureCount, error: any) => {
      // Don't retry if user not found
      if (error?.response?.status === 404) {
        return false
      }
      return failureCount < 3
    },
  })
}