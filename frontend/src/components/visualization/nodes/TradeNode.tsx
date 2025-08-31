"use client"

import { Handle, Position } from '@xyflow/react'
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ArrowRightLeft } from 'lucide-react'

interface TradeNodeData {
  label: string
  tradeId: string
  timestamp: number
  participants: string[]
}

export function TradeNode({ data }: { data: TradeNodeData }) {
  const formatDate = (timestamp: number) => {
    return new Date(timestamp).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  }

  return (
    <div className="min-w-48">
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 bg-orange-500"
      />
      
      <Card className="border-2 border-orange-500 bg-orange-50">
        <CardContent className="p-3">
          <div className="flex items-center gap-2 mb-2">
            <ArrowRightLeft className="h-4 w-4 text-orange-600" />
            <Badge variant="outline" className="bg-orange-100 text-orange-800">
              Trade
            </Badge>
          </div>
          
          <div className="space-y-1">
            <h4 className="font-semibold text-sm text-orange-900">
              {data.label}
            </h4>
            <p className="text-xs text-orange-700">
              {formatDate(data.timestamp)}
            </p>
            <p className="text-xs text-orange-600">
              {data.participants.length} teams involved
            </p>
          </div>
        </CardContent>
      </Card>

      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 bg-orange-500"
      />
    </div>
  )
}