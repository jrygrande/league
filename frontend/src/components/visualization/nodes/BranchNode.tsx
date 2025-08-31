"use client"

import { Handle, Position } from '@xyflow/react'
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { GitBranch } from 'lucide-react'

interface BranchNodeData {
  label: string
  initialAsset: any
  outcomes: any[]
}

export function BranchNode({ data }: { data: BranchNodeData }) {
  return (
    <div className="min-w-48">
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 bg-purple-500"
      />
      
      <Card className="border-2 border-purple-500 bg-purple-50">
        <CardContent className="p-3">
          <div className="flex items-center gap-2 mb-2">
            <GitBranch className="h-4 w-4 text-purple-600" />
            <Badge variant="outline" className="bg-purple-100 text-purple-800">
              Branch
            </Badge>
          </div>
          
          <div className="space-y-1">
            <h4 className="font-semibold text-sm text-purple-900">
              {data.label}
            </h4>
            <p className="text-xs text-purple-700">
              {data.outcomes.length} outcome{data.outcomes.length !== 1 ? 's' : ''}
            </p>
            {data.initialAsset?.asset_name && (
              <p className="text-xs text-purple-600">
                From: {data.initialAsset.asset_name}
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 bg-purple-500"
      />
    </div>
  )
}