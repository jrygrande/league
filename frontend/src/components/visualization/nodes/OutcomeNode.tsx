"use client"

import { Handle, Position } from '@xyflow/react'
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Target, Crown } from 'lucide-react'

interface OutcomeNodeData {
  label: string
  assetType: string
  currentOwner: string
  acquisition: string
  isCurrentOwner?: boolean
}

export function OutcomeNode({ data }: { data: OutcomeNodeData }) {
  const getAssetTypeColor = (assetType: string) => {
    switch (assetType?.toLowerCase()) {
      case 'player':
        return 'bg-blue-100 text-blue-800'
      case 'pick':
        return 'bg-green-100 text-green-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const isCurrentOwnerNode = data.isCurrentOwner

  return (
    <div className="min-w-48">
      <Handle
        type="target"
        position={Position.Top}
        className={`w-3 h-3 ${isCurrentOwnerNode ? 'bg-gold-500' : 'bg-gray-500'}`}
      />
      
      <Card className={`border-2 ${isCurrentOwnerNode 
        ? 'border-yellow-500 bg-yellow-50' 
        : 'border-gray-400 bg-gray-50'
      }`}>
        <CardContent className="p-3">
          <div className="flex items-center gap-2 mb-2">
            {isCurrentOwnerNode ? (
              <Crown className="h-4 w-4 text-yellow-600" />
            ) : (
              <Target className="h-4 w-4 text-gray-600" />
            )}
            <Badge className={getAssetTypeColor(data.assetType)}>
              {data.assetType || 'Asset'}
            </Badge>
          </div>
          
          <div className="space-y-1">
            <h4 className={`font-semibold text-sm ${isCurrentOwnerNode 
              ? 'text-yellow-900' 
              : 'text-gray-900'
            }`}>
              {data.label}
            </h4>
            <p className={`text-xs ${isCurrentOwnerNode 
              ? 'text-yellow-700' 
              : 'text-gray-700'
            }`}>
              Owner: {data.currentOwner}
            </p>
            {data.acquisition && (
              <p className={`text-xs ${isCurrentOwnerNode 
                ? 'text-yellow-600' 
                : 'text-gray-600'
              }`}>
                Via: {data.acquisition}
              </p>
            )}
            {isCurrentOwnerNode && (
              <Badge variant="outline" className="bg-yellow-100 text-yellow-800 text-xs">
                Current Owner
              </Badge>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}