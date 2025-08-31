import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'
import { QUERY_KEYS, User } from '@/lib/types'

export function useUser(username: string) {
  return useQuery({
    queryKey: QUERY_KEYS.user(username),
    queryFn: () => apiClient.getUserByUsername(username),
    enabled: !!username && username.length > 0,
    retry: (failureCount, error: any) => {
      // Don't retry if user not found
      if (error?.response?.status === 404) {
        return false
      }
      return failureCount < 3
    },
  })
}