'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'
import dynamic from 'next/dynamic'

const ReactQueryDevtools = dynamic(
  () => import('@tanstack/react-query-devtools').then((m) => ({ 
    default: m.ReactQueryDevtools 
  })),
  { ssr: false }
)

interface ProvidersProps {
  children: React.ReactNode
}

export function Providers({ children }: ProvidersProps) {
  const [queryClient] = useState(
    () => new QueryClient({
      defaultOptions: {
        queries: {
          // Stale time of 5 minutes
          staleTime: 1000 * 60 * 5,
          // Cache time of 10 minutes
          gcTime: 1000 * 60 * 10,
          // Retry failed requests 3 times
          retry: 3,
          // Retry with exponential backoff
          retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
          // Refetch on window focus in production
          refetchOnWindowFocus: process.env.NODE_ENV === 'production',
        },
        mutations: {
          retry: 1,
        },
      },
    })
  )

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {process.env.NODE_ENV === 'development' && (
        <ReactQueryDevtools initialIsOpen={false} />
      )}
    </QueryClientProvider>
  )
}