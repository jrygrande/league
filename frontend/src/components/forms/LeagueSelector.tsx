"use client"

import { useState } from "react"
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
import { useUserLeagues } from "@/hooks/useUserLeagues"
import { League, User } from "@/lib/types"

interface LeagueSelectorProps {
  user: User
  onLeagueSelected: (league: League) => void
  selectedLeague?: League
}

export function LeagueSelector({ user, onLeagueSelected, selectedLeague }: LeagueSelectorProps) {
  const [selectedSeason, setSelectedSeason] = useState("2024")
  const currentYear = new Date().getFullYear()
  const seasons = Array.from({ length: 5 }, (_, i) => (currentYear - i).toString())

  const {
    data: leagues,
    isLoading,
    error,
  } = useUserLeagues(user.username, selectedSeason)

  const handleLeagueSelect = (leagueId: string) => {
    const league = leagues?.find(l => l.league_id === leagueId)
    if (league) {
      onLeagueSelected(league)
    }
  }

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

  return (
    <div className="w-full max-w-2xl space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Select League</CardTitle>
          <CardDescription>
            Choose a season and league for {user.display_name || user.username}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Season Selector */}
          <div className="space-y-2">
            <label htmlFor="season" className="text-sm font-medium">
              Season
            </label>
            <Select value={selectedSeason} onValueChange={setSelectedSeason}>
              <SelectTrigger>
                <SelectValue placeholder="Select season" />
              </SelectTrigger>
              <SelectContent>
                {seasons.map((season) => (
                  <SelectItem key={season} value={season}>
                    {season}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

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

            {leagues && leagues.length === 0 && (
              <Alert>
                <AlertDescription>
                  No leagues found for {selectedSeason}. Try selecting a different season.
                </AlertDescription>
              </Alert>
            )}

            {leagues && leagues.length > 0 && (
              <Select
                value={selectedLeague?.league_id || ""}
                onValueChange={handleLeagueSelect}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a league" />
                </SelectTrigger>
                <SelectContent>
                  {leagues.map((league) => (
                    <SelectItem key={league.league_id} value={league.league_id}>
                      <div className="flex items-center gap-2">
                        <span>{league.name}</span>
                        <span className="text-sm text-muted-foreground">
                          ({league.total_rosters} teams)
                        </span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </div>

          {/* Selected League Details */}
          {selectedLeague && (
            <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="space-y-3">
                <div className="flex items-start justify-between">
                  <div>
                    <h4 className="font-medium text-blue-900">{selectedLeague.name}</h4>
                    <p className="text-sm text-blue-700">
                      Season {selectedLeague.season} • {selectedLeague.total_rosters} teams
                    </p>
                  </div>
                  {getLeagueStatus(selectedLeague.status)}
                </div>
                
                <div className="flex flex-wrap gap-2">
                  <Badge variant="outline">
                    {getScoringType(selectedLeague.scoring_settings)}
                  </Badge>
                  {selectedLeague.settings?.playoff_teams && (
                    <Badge variant="outline">
                      {selectedLeague.settings.playoff_teams} playoff teams
                    </Badge>
                  )}
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}