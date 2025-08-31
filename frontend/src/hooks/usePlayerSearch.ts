import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'
import { QUERY_KEYS } from '@/lib/types'
import { useMemo } from 'react'
import { useDebounce } from './useDebounce'

export function usePlayerSearch(query: string) {
  // Debounce the search query to avoid too many API calls
  const debouncedQuery = useDebounce(query, 300)
  
  const queryResult = useQuery({
    queryKey: QUERY_KEYS.playerSearch(debouncedQuery),
    queryFn: () => apiClient.searchPlayers(debouncedQuery),
    enabled: debouncedQuery.length >= 2,
    staleTime: 1000 * 60 * 5, // 5 minutes
  })

  // Memoize the results to prevent unnecessary re-renders
  const results = useMemo(() => {
    if (!queryResult.data) return []
    return queryResult.data
  }, [queryResult.data])

  return {
    ...queryResult,
    data: results,
  }
}