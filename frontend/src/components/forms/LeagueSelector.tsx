"use client"

import { useState, useEffect } from "react"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Skeleton } from "@/components/ui/skeleton"
import { useAllUserLeagues } from "@/hooks/useAllUserLeagues"
import { useLeagueHistory } from "@/hooks/useLeagueHistory"
import { LeagueChain, LeagueHistory, User } from "@/lib/types"

interface LeagueSelectorProps {
  user: User
  onLeagueSelected: (leagueChain: LeagueChain, leagueHistory: LeagueHistory) => void
  selectedLeagueChain?: LeagueChain | null
}

export function LeagueSelector({ user, onLeagueSelected, selectedLeagueChain }: LeagueSelectorProps) {
  const [selectedLeagueId, setSelectedLeagueId] = useState<string>("")

  const {
    data: allLeaguesResponse,
    isLoading: isLoadingLeagues,
    error: leaguesError,
  } = useAllUserLeagues(user.username)

  const {
    data: leagueHistory,
    isLoading: isLoadingHistory,
    error: historyError,
  } = useLeagueHistory(selectedLeagueId)

  const handleLeagueSelect = (baseLeagueId: string) => {
    const leagueChain = allLeaguesResponse?.league_chains.find(chain => chain.base_league_id === baseLeagueId)
    if (leagueChain) {
      setSelectedLeagueId(baseLeagueId)
      // Once we have both the league chain and its history, call the callback
      if (leagueHistory) {
        onLeagueSelected(leagueChain, leagueHistory)
      }
    }
  }

  // Effect to call onLeagueSelected when both league chain and history are available
  useEffect(() => {
    const selectedChain = allLeaguesResponse?.league_chains.find(chain => chain.base_league_id === selectedLeagueId)
    if (selectedChain && leagueHistory) {
      onLeagueSelected(selectedChain, leagueHistory)
    }
  }, [selectedLeagueId, allLeaguesResponse, leagueHistory, onLeagueSelected])

  const getLeagueStatus = (status: string) => {
    switch (status) {
      case "complete":
        return <Badge variant="default" className="bg-green-100 text-green-800">Complete</Badge>
      case "in_season":
        return <Badge variant="default" className="bg-blue-100 text-blue-800">In Season</Badge>
      case "drafting":
        return <Badge variant="default" className="bg-orange-100 text-orange-800">Drafting</Badge>
      case "pre_draft":
        return <Badge variant="secondary">Pre-Draft</Badge>
      default:
        return <Badge variant="outline">{status}</Badge>
    }
  }

  const getScoringType = (settings: Record<string, any>) => {
    if (settings.type === 1) return "PPR"
    if (settings.type === 0.5) return "0.5 PPR" 
    if (settings.type === 0) return "Standard"
    return "Custom"
  }

  const isLoading = isLoadingLeagues || (selectedLeagueId && isLoadingHistory)
  const error = leaguesError || historyError

  return (
    <div className="w-full max-w-2xl space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Select League</CardTitle>
          <CardDescription>
            Choose a league for {user.display_name || user.username} - all seasons included
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* League Selector */}
          <div className="space-y-2">
            <label htmlFor="league" className="text-sm font-medium">
              League
            </label>
            
            {isLoading && (
              <div className="space-y-2">
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-4 w-3/4" />
              </div>
            )}

            {error && (
              <Alert variant="destructive">
                <AlertDescription>
                  Failed to load leagues. Please try again.
                </AlertDescription>
              </Alert>
            )}

            {allLeaguesResponse && allLeaguesResponse.league_chains.length === 0 && (
              <Alert>
                <AlertDescription>
                  No leagues found for {user.display_name || user.username}. You may need to join some leagues first.
                </AlertDescription>
              </Alert>
            )}

            {allLeaguesResponse && allLeaguesResponse.league_chains.length > 0 && (
              <Select
                value={selectedLeagueChain?.base_league_id || ""}
                onValueChange={handleLeagueSelect}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a league" />
                </SelectTrigger>
                <SelectContent>
                  {allLeaguesResponse.league_chains.map((leagueChain) => (
                    <SelectItem key={leagueChain.base_league_id} value={leagueChain.base_league_id}>
                      <div className="flex items-center gap-2">
                        <span>{leagueChain.name}</span>
                        <span className="text-sm text-muted-foreground">
                          ({leagueChain.total_rosters} teams)
                        </span>
                        {leagueChain.total_seasons > 1 && (
                          <Badge variant="outline" className="text-xs">
                            {leagueChain.total_seasons} seasons
                          </Badge>
                        )}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </div>

          {/* Selected League Details */}
          {selectedLeagueChain && (
            <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="space-y-3">
                <div className="flex items-start justify-between">
                  <div>
                    <h4 className="font-medium text-blue-900">{selectedLeagueChain.name}</h4>
                    <p className="text-sm text-blue-700">
                      {selectedLeagueChain.total_seasons > 1 ? (
                        <>Seasons {Math.min(...selectedLeagueChain.seasons.map(s => parseInt(s)))}-{selectedLeagueChain.most_recent_season}</>
                      ) : (
                        <>Season {selectedLeagueChain.most_recent_season}</>
                      )} • {selectedLeagueChain.total_rosters} teams
                    </p>
                  </div>
                  {getLeagueStatus(selectedLeagueChain.status)}
                </div>
                
                <div className="flex flex-wrap gap-2">
                  {selectedLeagueChain.total_seasons > 1 && (
                    <Badge variant="default" className="bg-blue-100 text-blue-800">
                      {selectedLeagueChain.total_seasons} Season Dynasty
                    </Badge>
                  )}
                  <Badge variant="outline">
                    {selectedLeagueChain.total_rosters} teams
                  </Badge>
                  {leagueHistory && (
                    <Badge variant="outline" className="bg-green-100 text-green-800">
                      Full History Loaded
                    </Badge>
                  )}
                </div>
                
                {selectedLeagueChain.total_seasons > 1 && (
                  <div className="text-xs text-blue-600">
                    Seasons: {selectedLeagueChain.seasons.join(', ')}
                  </div>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}