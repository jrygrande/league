"use client"

import { useState, useEffect } from "react"
import { UsernameForm, LeagueSelector } from "@/components/forms"
import { PlayerSearch } from "@/components/search"
import { AssetChainVisualization } from "@/components/visualization/AssetChainVisualization"
import { ChainSummary } from "@/components/visualization/ChainSummary"
import { User, League, Player, Roster } from "@/lib/types"
import { useLeagueRosters } from "@/hooks/useLeagueRosters"
import { useAssetChain } from "@/hooks/useAssetChain"
import { Button } from "@/components/ui/button"
import { ArrowLeft } from "lucide-react"

export default function Home() {
  const [currentStep, setCurrentStep] = useState<'username' | 'league' | 'player' | 'results'>('username')
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [selectedLeague, setSelectedLeague] = useState<League | null>(null)
  const [selectedPlayer, setSelectedPlayer] = useState<Player | null>(null)
  const [userRoster, setUserRoster] = useState<Roster | null>(null)

  // Fetch rosters when league is selected
  const { data: rosters } = useLeagueRosters(selectedLeague?.league_id || '')

  // Update userRoster when rosters data changes
  useEffect(() => {
    if (rosters && selectedUser && selectedLeague) {
      const userRosterInLeague = rosters.find(roster => roster.owner_id === selectedUser.user_id)
      setUserRoster(userRosterInLeague || null)
    }
  }, [rosters, selectedUser, selectedLeague])

  const handleUserFound = (user: User) => {
    setSelectedUser(user)
    setCurrentStep('league')
  }

  const handleLeagueSelected = (league: League) => {
    setSelectedLeague(league)
    setCurrentStep('player')
    
    // Find user's roster in this league (will be set when rosters are loaded)
    if (rosters && selectedUser) {
      const userRosterInLeague = rosters.find(roster => roster.owner_id === selectedUser.user_id)
      setUserRoster(userRosterInLeague || null)
    }
  }

  const handlePlayerSelected = (player: Player) => {
    setSelectedPlayer(player)
    setCurrentStep('results')
  }

  const goBack = () => {
    switch (currentStep) {
      case 'league':
        setCurrentStep('username')
        setSelectedUser(null)
        break
      case 'player':
        setCurrentStep('league')
        setSelectedLeague(null)
        break
      case 'results':
        setCurrentStep('player')
        setSelectedPlayer(null)
        break
    }
  }

  const reset = () => {
    setCurrentStep('username')
    setSelectedUser(null)
    setSelectedLeague(null)
    setSelectedPlayer(null)
    setUserRoster(null)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              Sleeper League Explorer
            </h1>
            <p className="text-xl text-gray-600">
              Visualize player trade lineages and fantasy football analytics
            </p>
          </div>

          {/* Step Indicator */}
          <div className="flex items-center justify-center mb-8">
            <div className="flex items-center space-x-4">
              {[
                { key: 'username', label: 'User', active: currentStep === 'username' || !!selectedUser },
                { key: 'league', label: 'League', active: currentStep === 'league' || !!selectedLeague },
                { key: 'player', label: 'Player', active: currentStep === 'player' || !!selectedPlayer },
                { key: 'results', label: 'Analysis', active: currentStep === 'results' },
              ].map((step, index) => (
                <div key={step.key} className="flex items-center">
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                      step.active
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-200 text-gray-600'
                    }`}
                  >
                    {index + 1}
                  </div>
                  <span className={`ml-2 text-sm font-medium ${
                    step.active ? 'text-blue-600' : 'text-gray-500'
                  }`}>
                    {step.label}
                  </span>
                  {index < 3 && (
                    <div className={`w-8 h-px mx-4 ${
                      step.active ? 'bg-blue-600' : 'bg-gray-300'
                    }`} />
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Back Button */}
          {currentStep !== 'username' && (
            <div className="mb-6">
              <Button
                variant="outline"
                onClick={goBack}
                className="flex items-center gap-2"
              >
                <ArrowLeft className="h-4 w-4" />
                Back
              </Button>
            </div>
          )}

          {/* Current Step Content */}
          <div className="flex justify-center">
            {currentStep === 'username' && (
              <UsernameForm onUserFound={handleUserFound} />
            )}

            {currentStep === 'league' && selectedUser && (
              <LeagueSelector
                user={selectedUser}
                onLeagueSelected={handleLeagueSelected}
              />
            )}

            {currentStep === 'player' && selectedUser && selectedLeague && (
              <PlayerSearch onPlayerSelected={handlePlayerSelected} />
            )}

            {currentStep === 'results' && selectedUser && selectedLeague && selectedPlayer && userRoster && (
              <div className="w-full max-w-6xl space-y-6">
                {/* Header with basic info */}
                <div className="bg-white rounded-lg border shadow-sm p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-2xl font-bold text-gray-900">
                      Asset Chain Analysis
                    </h2>
                    <Button onClick={reset} variant="outline">
                      Start New Analysis
                    </Button>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="font-medium text-gray-600">User:</span>{' '}
                      {selectedUser.display_name || selectedUser.username}
                    </div>
                    <div>
                      <span className="font-medium text-gray-600">League:</span>{' '}
                      {selectedLeague.name} ({selectedLeague.season})
                    </div>
                    <div>
                      <span className="font-medium text-gray-600">Player:</span>{' '}
                      {selectedPlayer.full_name || `${selectedPlayer.first_name} ${selectedPlayer.last_name}`}
                    </div>
                  </div>
                </div>

                {/* Asset Chain Visualization */}
                <AssetChainVisualization
                  leagueId={selectedLeague.league_id}
                  rosterId={userRoster.roster_id}
                  assetId={selectedPlayer.player_id}
                  assetName={selectedPlayer.full_name || `${selectedPlayer.first_name} ${selectedPlayer.last_name}`}
                />

                {/* Chain Summary - only show if we have asset chain data */}
                <AssetChainSummaryWrapper
                  leagueId={selectedLeague.league_id}
                  rosterId={userRoster.roster_id}
                  assetId={selectedPlayer.player_id}
                />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// Helper component to conditionally render ChainSummary
function AssetChainSummaryWrapper({ 
  leagueId, 
  rosterId, 
  assetId 
}: { 
  leagueId: string
  rosterId: number
  assetId: string 
}) {
  const { data: assetChain } = useAssetChain(leagueId, rosterId, assetId)
  
  if (!assetChain) {
    return null
  }
  
  return <ChainSummary assetChain={assetChain} />
}