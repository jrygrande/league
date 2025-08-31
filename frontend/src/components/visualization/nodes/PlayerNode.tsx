"use client"

import { Handle, Position } from '@xyflow/react'
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { User } from 'lucide-react'

interface PlayerNodeData {
  label: string
  assetType: string
  acquisition: any
  managerName: string
}

export function PlayerNode({ data }: { data: PlayerNodeData }) {
  const getAssetTypeColor = (assetType: string) => {
    switch (assetType.toLowerCase()) {
      case 'player':
        return 'bg-blue-100 text-blue-800'
      case 'pick':
        return 'bg-green-100 text-green-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getAcquisitionMethod = (acquisition: any) => {
    if (!acquisition) return 'Unknown'
    if (acquisition.method) return acquisition.method
    if (acquisition.type) return acquisition.type
    return 'Draft/Original'
  }

  return (
    <div className="min-w-48">
      <Card className="border-2 border-blue-500 bg-blue-50">
        <CardContent className="p-3">
          <div className="flex items-center gap-2 mb-2">
            <User className="h-4 w-4 text-blue-600" />
            <Badge className={getAssetTypeColor(data.assetType)}>
              {data.assetType}
            </Badge>
          </div>
          
          <div className="space-y-1">
            <h4 className="font-semibold text-sm text-blue-900">
              {data.label}
            </h4>
            <p className="text-xs text-blue-700">
              Owner: {data.managerName}
            </p>
            <p className="text-xs text-blue-600">
              Via: {getAcquisitionMethod(data.acquisition)}
            </p>
          </div>
        </CardContent>
      </Card>
      
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 bg-blue-500"
      />
    </div>
  )
}