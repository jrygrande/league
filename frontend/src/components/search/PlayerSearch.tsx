"use client"

import { useState } from "react"
import { Check, Search, User } from "lucide-react"
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"
import { usePlayerSearch } from "@/hooks/usePlayerSearch"
import { Player } from "@/lib/types"

interface PlayerSearchProps {
  onPlayerSelected: (player: Player) => void
  selectedPlayer?: Player
}

export function PlayerSearch({ onPlayerSelected, selectedPlayer }: PlayerSearchProps) {
  const [open, setOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")

  const { data: players, isLoading, error, isPending } = usePlayerSearch(searchQuery)

  // Debug logging
  console.log('PlayerSearch render:', {
    searchQuery,
    playersLength: players?.length || 0,
    isLoading,
    isPending,
    error: error?.message
  })

  const handlePlayerSelect = (player: Player) => {
    onPlayerSelected(player)
    setOpen(false)
    setSearchQuery("")
  }

  const getPositionColor = (position?: string) => {
    switch (position) {
      case "QB":
        return "bg-red-100 text-red-800"
      case "RB":
        return "bg-green-100 text-green-800"  
      case "WR":
        return "bg-blue-100 text-blue-800"
      case "TE":
        return "bg-yellow-100 text-yellow-800"
      case "K":
        return "bg-purple-100 text-purple-800"
      case "DEF":
        return "bg-gray-100 text-gray-800"
      default:
        return "bg-gray-100 text-gray-600"
    }
  }

  const formatPlayerName = (player: Player) => {
    return player.full_name || `${player.first_name || ''} ${player.last_name || ''}`.trim() || 'Unknown Player'
  }

  return (
    <div className="w-full max-w-2xl space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Search for Player</CardTitle>
          <CardDescription>
            Find a player to analyze their trade lineage and asset chain
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Popover open={open} onOpenChange={setOpen}>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  role="combobox"
                  aria-expanded={open}
                  className="w-full justify-between"
                >
                  {selectedPlayer ? (
                    <div className="flex items-center gap-2">
                      <User className="h-4 w-4 text-muted-foreground" />
                      <span>{formatPlayerName(selectedPlayer)}</span>
                      {selectedPlayer.position && (
                        <Badge variant="outline" className={cn("text-xs", getPositionColor(selectedPlayer.position))}>
                          {selectedPlayer.position}
                        </Badge>
                      )}
                      {selectedPlayer.team && (
                        <Badge variant="outline" className="text-xs">
                          {selectedPlayer.team}
                        </Badge>
                      )}
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <Search className="h-4 w-4" />
                      <span>Search for a player...</span>
                    </div>
                  )}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-full p-0" align="start">
                <Command shouldFilter={false}>
                  <CommandInput
                    placeholder="Type player name..."
                    value={searchQuery}
                    onValueChange={setSearchQuery}
                  />
                  <CommandList>
                    {(isLoading || isPending) && searchQuery.length >= 2 && (
                      <div className="p-4 space-y-2">
                        <Skeleton className="h-4 w-full" />
                        <Skeleton className="h-4 w-3/4" />
                        <Skeleton className="h-4 w-1/2" />
                      </div>
                    )}

                    {error && !isPending && (
                      <div className="p-4 text-sm text-red-600">
                        Failed to search players. Please try again.
                      </div>
                    )}

                    {searchQuery.length < 2 && !isLoading && !isPending && (
                      <CommandEmpty>Type at least 2 characters to search...</CommandEmpty>
                    )}

                    {searchQuery.length >= 2 && !isLoading && !isPending && players?.length === 0 && (
                      <CommandEmpty>No players found for "{searchQuery}"</CommandEmpty>
                    )}

                    {players && players.length > 0 && (
                      <CommandGroup>
                        <div className={cn("relative", isPending && "opacity-75")}>
                          {players.slice(0, 10).map((player) => (
                            <CommandItem
                              key={player.player_id}
                              onSelect={() => handlePlayerSelect(player)}
                              className="flex items-center justify-between p-3"
                            >
                              <div className="flex items-center gap-3">
                                <div className="flex-1">
                                  <div className="font-medium">
                                    {formatPlayerName(player)}
                                  </div>
                                  <div className="flex items-center gap-2 mt-1">
                                    {player.position && (
                                      <Badge variant="outline" className={cn("text-xs", getPositionColor(player.position))}>
                                        {player.position}
                                      </Badge>
                                    )}
                                    {player.team && (
                                      <Badge variant="outline" className="text-xs">
                                        {player.team}
                                      </Badge>
                                    )}
                                    {player.age && (
                                      <span className="text-xs text-muted-foreground">
                                        Age {player.age}
                                      </span>
                                    )}
                                  </div>
                                </div>
                              </div>
                              <Check
                                className={cn(
                                  "h-4 w-4",
                                  selectedPlayer?.player_id === player.player_id
                                    ? "opacity-100"
                                    : "opacity-0"
                                )}
                              />
                            </CommandItem>
                          ))}
                          {isPending && (
                            <div className="absolute top-0 right-0 p-2">
                              <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
                            </div>
                          )}
                        </div>
                      </CommandGroup>
                    )}
                  </CommandList>
                </Command>
              </PopoverContent>
            </Popover>

            {/* Selected Player Details */}
            {selectedPlayer && (
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium text-blue-900">
                      {formatPlayerName(selectedPlayer)}
                    </h4>
                    <div className="flex items-center gap-2 mt-1">
                      {selectedPlayer.position && (
                        <Badge className={cn("text-xs", getPositionColor(selectedPlayer.position))}>
                          {selectedPlayer.position}
                        </Badge>
                      )}
                      {selectedPlayer.team && (
                        <Badge variant="outline" className="text-xs">
                          {selectedPlayer.team}
                        </Badge>
                      )}
                      {selectedPlayer.age && (
                        <span className="text-sm text-blue-700">
                          Age {selectedPlayer.age}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}