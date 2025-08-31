"use client"

import { useState } from "react"
import { UsernameForm, LeagueSelector } from "@/components/forms"
import { PlayerSearch } from "@/components/search"
import { User, League, Player } from "@/lib/types"
import { Button } from "@/components/ui/button"
import { ArrowLeft } from "lucide-react"

export default function Home() {
  const [currentStep, setCurrentStep] = useState<'username' | 'league' | 'player' | 'results'>('username')
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [selectedLeague, setSelectedLeague] = useState<League | null>(null)
  const [selectedPlayer, setSelectedPlayer] = useState<Player | null>(null)

  const handleUserFound = (user: User) => {
    setSelectedUser(user)
    setCurrentStep('league')
  }

  const handleLeagueSelected = (league: League) => {
    setSelectedLeague(league)
    setCurrentStep('player')
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

            {currentStep === 'results' && selectedUser && selectedLeague && selectedPlayer && (
              <div className="w-full max-w-2xl">
                <div className="bg-white rounded-lg border shadow-sm p-8 text-center">
                  <h2 className="text-2xl font-bold text-gray-900 mb-4">
                    Analysis Coming Soon!
                  </h2>
                  <div className="space-y-2 text-left bg-gray-50 p-4 rounded-lg mb-6">
                    <p><strong>User:</strong> {selectedUser.display_name || selectedUser.username}</p>
                    <p><strong>League:</strong> {selectedLeague.name} ({selectedLeague.season})</p>
                    <p><strong>Player:</strong> {selectedPlayer.full_name || `${selectedPlayer.first_name} ${selectedPlayer.last_name}`}</p>
                  </div>
                  <p className="text-gray-600 mb-6">
                    The asset chain visualization will be implemented in Phase 4 of the development process.
                    This will show the complete trade lineage and asset history for the selected player.
                  </p>
                  <Button onClick={reset} className="w-full">
                    Start New Analysis
                  </Button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}