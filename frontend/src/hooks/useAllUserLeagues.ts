import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'
import { QUERY_KEYS } from '@/lib/types'

export function useAllUserLeagues(username: string) {
  return useQuery({
    queryKey: QUERY_KEYS.allUserLeagues(username),
    queryFn: () => apiClient.getAllUserLeagues(username),
    enabled: !!username,
    retry: (failureCount, error: any) => {
      // Don't retry if user not found
      if (error?.response?.status === 404) {
        return false
      }
      return failureCount < 3
    },
    // This data changes infrequently - leagues don't get created/deleted often
    staleTime: 1000 * 60 * 15, // 15 minutes
  })
}