'use client'

import { useState } from 'react'
import { useUser } from '@/hooks/useUser'
import { useUserLeagues } from '@/hooks/useUserLeagues'
import { usePlayerSearch } from '@/hooks/usePlayerSearch'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'

export default function TestPage() {
  const [username, setUsername] = useState('testuser')
  const [playerQuery, setPlayerQuery] = useState('')
  const [enableUserQuery, setEnableUserQuery] = useState(false)

  // Test user hook
  const { data: user, isLoading: userLoading, error: userError } = useUser(
    enableUserQuery ? username : ''
  )

  // Test user leagues hook (only if user exists)
  const { data: leagues, isLoading: leaguesLoading, error: leaguesError } = useUserLeagues(
    enableUserQuery && user ? username : '',
    '2024'
  )

  // Test player search hook
  const { data: players, isLoading: playersLoading, error: playersError } = usePlayerSearch(playerQuery)

  return (
    <div className="container mx-auto p-6 space-y-6">
      <h1 className="text-3xl font-bold text-center">Frontend Integration Test</h1>
      
      {/* User Testing Section */}
      <Card>
        <CardHeader>
          <CardTitle>User API Test</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              placeholder="Enter username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
            <Button
              onClick={() => setEnableUserQuery(!enableUserQuery)}
              variant={enableUserQuery ? "destructive" : "default"}
            >
              {enableUserQuery ? 'Stop' : 'Test User API'}
            </Button>
          </div>

          {userLoading && <Skeleton className="h-20 w-full" />}
          
          {userError && (
            <Alert variant="destructive">
              <AlertDescription>
                Error: {userError.message}
              </AlertDescription>
            </Alert>
          )}
          
          {user && (
            <Card>
              <CardContent className="pt-4">
                <pre className="text-sm bg-muted p-3 rounded">
                  {JSON.stringify(user, null, 2)}
                </pre>
              </CardContent>
            </Card>
          )}

          {/* Leagues Section */}
          {enableUserQuery && user && (
            <div className="space-y-2">
              <h4 className="font-semibold">User's 2024 Leagues:</h4>
              {leaguesLoading && <Skeleton className="h-16 w-full" />}
              
              {leaguesError && (
                <Alert variant="destructive">
                  <AlertDescription>
                    Leagues Error: {leaguesError.message}
                  </AlertDescription>
                </Alert>
              )}
              
              {leagues && (
                <Card>
                  <CardContent className="pt-4">
                    <div className="text-sm">
                      <strong>Found {leagues.length} leagues:</strong>
                      {leagues.slice(0, 3).map((league, idx) => (
                        <div key={idx} className="mt-2 p-2 bg-muted rounded">
                          <strong>{league.name}</strong> - {league.total_rosters} teams
                        </div>
                      ))}
                      {leagues.length > 3 && (
                        <p className="text-muted-foreground mt-2">
                          ... and {leagues.length - 3} more leagues
                        </p>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Player Search Testing Section */}
      <Card>
        <CardHeader>
          <CardTitle>Player Search Test</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Input
            placeholder="Search for players (e.g., 'mahomes', 'kelce')"
            value={playerQuery}
            onChange={(e) => setPlayerQuery(e.target.value)}
          />

          {playersLoading && <Skeleton className="h-16 w-full" />}
          
          {playersError && (
            <Alert variant="destructive">
              <AlertDescription>
                Player Search Error: {playersError.message}
              </AlertDescription>
            </Alert>
          )}
          
          {players && players.length > 0 && (
            <Card>
              <CardContent className="pt-4">
                <div className="text-sm space-y-2">
                  <strong>Found {players.length} players:</strong>
                  {players.map((player) => (
                    <div key={player.player_id} className="p-2 bg-muted rounded">
                      <strong>{player.full_name}</strong> - {player.position} 
                      {player.team && ` (${player.team})`}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
          
          {playerQuery.length >= 2 && players && players.length === 0 && !playersLoading && (
            <Alert>
              <AlertDescription>
                No players found for "{playerQuery}"
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Component Testing Section */}
      <Card>
        <CardHeader>
          <CardTitle>shadcn/ui Components Test</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Button variant="default">Default</Button>
            <Button variant="secondary">Secondary</Button>
            <Button variant="outline">Outline</Button>
            <Button variant="destructive">Destructive</Button>
          </div>
          
          <Alert>
            <AlertDescription>
              This is a default alert to test the Alert component.
            </AlertDescription>
          </Alert>
          
          <Alert variant="destructive">
            <AlertDescription>
              This is a destructive alert variant.
            </AlertDescription>
          </Alert>
          
          <div className="space-y-2">
            <h4 className="font-semibold">Loading Skeletons:</h4>
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
          </div>
        </CardContent>
      </Card>
    </div>
  )
}