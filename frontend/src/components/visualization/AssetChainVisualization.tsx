"use client"

import { useCallback, useMemo } from 'react'
import {
  ReactFlow,
  Node,
  Edge,
  addEdge,
  Connection,
  useNodesState,
  useEdgesState,
  Controls,
  MiniMap,
  Background,
  BackgroundVariant,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { AlertCircle } from "lucide-react"
import { useAssetChain } from "@/hooks/useAssetChain"
import { ComprehensiveAssetChain } from "@/lib/types"

// Custom node types
import { PlayerNode } from './nodes/PlayerNode'
import { TradeNode } from './nodes/TradeNode'
import { BranchNode } from './nodes/BranchNode'
import { OutcomeNode } from './nodes/OutcomeNode'

const nodeTypes = {
  playerNode: PlayerNode,
  tradeNode: TradeNode,  
  branchNode: BranchNode,
  outcomeNode: OutcomeNode,
}

interface AssetChainVisualizationProps {
  leagueId: string
  rosterId: number
  assetId: string
  assetName: string
}

export function AssetChainVisualization({ 
  leagueId, 
  rosterId, 
  assetId, 
  assetName 
}: AssetChainVisualizationProps) {
  const { data: assetChain, isLoading, error } = useAssetChain(leagueId, rosterId, assetId)

  // Transform asset chain data into React Flow nodes and edges
  const { nodes, edges } = useMemo(() => {
    if (!assetChain) return { nodes: [], edges: [] }
    
    return transformAssetChainToFlow(assetChain)
  }, [assetChain])

  const [nodesState, setNodes, onNodesChange] = useNodesState(nodes)
  const [edgesState, setEdges, onEdgesChange] = useEdgesState(edges)

  const onConnect = useCallback((params: Connection) => {
    setEdges((eds) => addEdge(params, eds))
  }, [setEdges])

  if (isLoading) {
    return (
      <Card className="w-full h-96">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Skeleton className="h-4 w-4" />
            Loading Asset Chain for {assetName}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-8 w-3/4" />
            <Skeleton className="h-8 w-1/2" />
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Failed to load asset chain for {assetName}. This might mean no trade history exists for this asset.
        </AlertDescription>
      </Alert>
    )
  }

  if (!assetChain || nodes.length === 0) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle>No Trade History</CardTitle>
          <CardDescription>
            {assetName} doesn't appear to have any trade history in this league.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            This could mean the player was acquired through:
          </p>
          <ul className="mt-2 text-sm text-muted-foreground list-disc list-inside">
            <li>Original draft</li>
            <li>Waiver pickup</li>
            <li>Free agent addition</li>
          </ul>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="w-full space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            Trade Lineage: {assetName}
            <Badge variant="outline">
              {assetChain.asset_branches.length} Branch{assetChain.asset_branches.length !== 1 ? 'es' : ''}
            </Badge>
          </CardTitle>
          <CardDescription>
            Interactive visualization showing how {assetName} was acquired and traded
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-96 border rounded-lg">
            <ReactFlow
              nodes={nodesState}
              edges={edgesState}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              nodeTypes={nodeTypes}
              fitView
              attributionPosition="bottom-left"
            >
              <Controls />
              <MiniMap />
              <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
            </ReactFlow>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// Helper function to transform asset chain data into React Flow format
function transformAssetChainToFlow(assetChain: ComprehensiveAssetChain): { nodes: Node[], edges: Edge[] } {
  const nodes: Node[] = []
  const edges: Edge[] = []
  
  // Create root node for the original asset
  const rootNode: Node = {
    id: 'root',
    type: 'playerNode',
    position: { x: 250, y: 50 },
    data: {
      label: assetChain.asset_name,
      assetType: assetChain.asset_type,
      acquisition: assetChain.original_acquisition,
      managerName: assetChain.manager_name,
    },
  }
  nodes.push(rootNode)

  // Process asset branches
  let nodeId = 1
  let yOffset = 150

  assetChain.asset_branches.forEach((branch, branchIndex) => {
    // Create branch node
    const branchNodeId = `branch-${branchIndex}`
    const branchNode: Node = {
      id: branchNodeId,
      type: 'branchNode',
      position: { x: 100 + branchIndex * 300, y: yOffset },
      data: {
        label: `Branch ${branchIndex + 1}`,
        initialAsset: branch.initial_asset,
        outcomes: branch.final_outcomes,
      },
    }
    nodes.push(branchNode)

    // Connect root to branch
    edges.push({
      id: `root-to-${branchNodeId}`,
      source: 'root',
      target: branchNodeId,
      animated: true,
    })

    // Create outcome nodes for this branch
    branch.final_outcomes.forEach((outcome, outcomeIndex) => {
      const outcomeNodeId = `outcome-${branchIndex}-${outcomeIndex}`
      const outcomeNode: Node = {
        id: outcomeNodeId,
        type: 'outcomeNode',
        position: { 
          x: 50 + branchIndex * 300 + outcomeIndex * 150, 
          y: yOffset + 150 
        },
        data: {
          label: outcome.asset_name || `Asset ${outcomeIndex + 1}`,
          assetType: outcome.asset_type,
          currentOwner: outcome.current_owner,
          acquisition: outcome.acquisition_method,
        },
      }
      nodes.push(outcomeNode)

      // Connect branch to outcome
      edges.push({
        id: `${branchNodeId}-to-${outcomeNodeId}`,
        source: branchNodeId,
        target: outcomeNodeId,
      })
    })

    yOffset += 300
  })

  return { nodes, edges }
}