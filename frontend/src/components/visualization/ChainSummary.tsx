"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { 
  BarChart3, 
  TrendingUp, 
  Users, 
  Calendar,
  ArrowRightLeft,
  Target 
} from 'lucide-react'
import { ComprehensiveAssetChain } from "@/lib/types"

interface ChainSummaryProps {
  assetChain: ComprehensiveAssetChain
}

export function ChainSummary({ assetChain }: ChainSummaryProps) {
  // Calculate summary statistics
  const totalBranches = assetChain.asset_branches.length
  const totalOutcomes = assetChain.asset_branches.reduce(
    (total, branch) => total + branch.final_outcomes.length, 
    0
  )
  
  // Extract key information
  const originalAcquisition = assetChain.original_acquisition
  const currentManager = assetChain.manager_name
  const assetType = assetChain.asset_type
  
  // Get acquisition method
  const getAcquisitionMethod = (acquisition: any) => {
    if (!acquisition) return 'Unknown'
    if (acquisition.method) return acquisition.method
    if (acquisition.type) return acquisition.type
    if (acquisition.draft_round) return `Round ${acquisition.draft_round} Pick`
    return 'Original Owner'
  }

  // Get unique teams involved
  const teamsInvolved = new Set([currentManager])
  assetChain.asset_branches.forEach(branch => {
    branch.final_outcomes.forEach(outcome => {
      if (outcome.current_owner) {
        teamsInvolved.add(outcome.current_owner)
      }
    })
  })

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Asset Chain Summary
          </CardTitle>
          <CardDescription>
            Key statistics and timeline for {assetChain.asset_name}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          
          {/* Original Acquisition */}
          <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
            <div className="flex items-center gap-3">
              <Target className="h-4 w-4 text-blue-600" />
              <div>
                <p className="font-medium text-blue-900">Original Acquisition</p>
                <p className="text-sm text-blue-700">
                  {getAcquisitionMethod(originalAcquisition)}
                </p>
              </div>
            </div>
            <Badge className="bg-blue-100 text-blue-800">
              {assetType}
            </Badge>
          </div>

          <Separator />

          {/* Key Metrics Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center justify-center mb-1">
                <ArrowRightLeft className="h-4 w-4 text-gray-600" />
              </div>
              <p className="text-2xl font-bold text-gray-900">{totalBranches}</p>
              <p className="text-sm text-gray-600">Trade{totalBranches !== 1 ? 's' : ''}</p>
            </div>

            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center justify-center mb-1">
                <TrendingUp className="h-4 w-4 text-gray-600" />
              </div>
              <p className="text-2xl font-bold text-gray-900">{totalOutcomes}</p>
              <p className="text-sm text-gray-600">Asset{totalOutcomes !== 1 ? 's' : ''}</p>
            </div>

            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center justify-center mb-1">
                <Users className="h-4 w-4 text-gray-600" />
              </div>
              <p className="text-2xl font-bold text-gray-900">{teamsInvolved.size}</p>
              <p className="text-sm text-gray-600">Team{teamsInvolved.size !== 1 ? 's' : ''}</p>
            </div>

            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center justify-center mb-1">
                <Calendar className="h-4 w-4 text-gray-600" />
              </div>
              <p className="text-2xl font-bold text-gray-900">
                {assetChain.chain_summary?.season || 'N/A'}
              </p>
              <p className="text-sm text-gray-600">Season</p>
            </div>
          </div>

          {/* Current Status */}
          <div className="p-3 bg-green-50 rounded-lg">
            <div className="flex items-center gap-2 mb-1">
              <Badge className="bg-green-100 text-green-800">Current Status</Badge>
            </div>
            <p className="font-medium text-green-900">
              Owned by: {currentManager}
            </p>
            {assetChain.trade_away_details && (
              <p className="text-sm text-green-700 mt-1">
                Last traded: {new Date(assetChain.trade_away_details.timestamp).toLocaleDateString()}
              </p>
            )}
          </div>

          {/* Assets Received Summary */}
          {assetChain.assets_received && assetChain.assets_received.length > 0 && (
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Assets Received in Trades</h4>
              <div className="space-y-2">
                {assetChain.assets_received.map((asset, index) => (
                  <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="text-sm font-medium">
                      {asset.asset_name || `Asset ${index + 1}`}
                    </span>
                    <Badge variant="outline" className="text-xs">
                      {asset.asset_type || 'Unknown'}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}