"use client"

import { useCallback, useMemo } from 'react'
import {
  ReactFlow,
  ReactFlowProvider,
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
  useReactFlow,
  Panel,
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

  // Debug logging
  console.log('AssetChainVisualization render:', {
    leagueId,
    rosterId,
    assetId,
    assetName,
    assetChain,
    isLoading,
    error
  })

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
    // Check if this is a 404 (no trade history) vs actual error
    const is404 = error?.response?.status === 404
    
    if (is404) {
      return (
        <Card className="w-full">
          <CardHeader>
            <CardTitle>No Trade History</CardTitle>
            <CardDescription>
              {assetName} has no trade history in this league
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-3">
              This player was likely acquired through:
            </p>
            <ul className="text-sm text-muted-foreground list-disc list-inside space-y-1">
              <li>Original draft pick</li>
              <li>Waiver wire claim</li>
              <li>Free agent pickup</li>
            </ul>
          </CardContent>
        </Card>
      )
    }
    
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Failed to load asset chain for {assetName}. Error: {error?.message || 'Unknown error'}
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
          <div className="w-full h-96 border rounded-lg overflow-hidden">
            <ReactFlowProvider>
              <ReactFlow
                nodes={nodesState}
                edges={edgesState}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onConnect={onConnect}
                nodeTypes={nodeTypes}
                fitView
                attributionPosition="bottom-left"
                defaultViewport={{ x: 0, y: 0, zoom: 0.8 }}
                minZoom={0.1}
                maxZoom={2}
                style={{ width: '100%', height: '100%' }}
              >
                <Controls />
                <MiniMap />
                <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
                <Panel position="top-right" className="bg-white p-2 rounded text-xs text-gray-500">
                  Debug: {nodes.length} nodes, {edges.length} edges
                </Panel>
              </ReactFlow>
            </ReactFlowProvider>
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
  let nodeIdCounter = 0
  
  console.log('Transforming asset chain:', assetChain)
  
  // Create root node for the original asset
  const rootNode: Node = {
    id: 'root',
    type: 'playerNode',
    position: { x: 400, y: 50 },
    data: {
      label: assetChain.asset_name,
      assetType: assetChain.asset_type,
      acquisition: assetChain.original_acquisition,
      managerName: assetChain.manager_name,
    },
  }
  nodes.push(rootNode)

  // If no trades, show the asset as-is
  if (!assetChain.asset_branches || assetChain.asset_branches.length === 0) {
    console.log('No asset branches found')
    return { nodes, edges }
  }

  // Process each top-level branch recursively
  let xOffset = 100
  assetChain.asset_branches.forEach((branch, branchIndex) => {
    const { branchNodes, branchEdges, width } = processBranchRecursively(
      branch, 
      `branch-${branchIndex}`, 
      xOffset, 
      200, // yOffset 
      0, // depth
      nodeIdCounter
    )
    
    nodes.push(...branchNodes)
    edges.push(...branchEdges)
    
    // Connect root to this branch's first node
    if (branchNodes.length > 0) {
      edges.push({
        id: `root-to-${branchNodes[0].id}`,
        source: 'root',
        target: branchNodes[0].id,
        animated: true,
      })
    }
    
    xOffset += width + 100
    nodeIdCounter += 1000 // Ensure unique IDs across branches
  })

  console.log('Generated nodes:', nodes.length, 'edges:', edges.length)
  return { nodes, edges }
}

// Recursive function to process branches and sub-branches
function processBranchRecursively(
  branch: any,
  branchId: string,
  xStart: number,
  yStart: number,
  depth: number,
  baseNodeId: number
): { branchNodes: Node[], branchEdges: Edge[], width: number } {
  const branchNodes: Node[] = []
  const branchEdges: Edge[] = []
  
  console.log(`Processing branch at depth ${depth}:`, branch)
  
  // Create initial asset node (what was traded)
  const initialAssetNode: Node = {
    id: `${branchId}-initial`,
    type: 'playerNode',
    position: { x: xStart, y: yStart },
    data: {
      label: branch.initial_asset?.asset_name || 'Unknown Asset',
      assetType: branch.initial_asset?.asset_type || 'unknown',
      acquisition: 'Traded',
      managerName: 'Trading Away',
    },
  }
  branchNodes.push(initialAssetNode)
  
  let currentY = yStart + 100
  let maxWidth = 200
  
  // Show what was received in the trade (trade_package or assets_received_in_trade)
  const receivedAssets = branch.assets_received_in_trade || branch.trade_package || []
  receivedAssets.forEach((asset: any, index: number) => {
    const receivedNodeId = `${branchId}-received-${index}`
    const receivedNode: Node = {
      id: receivedNodeId,
      type: 'outcomeNode',
      position: { x: xStart + 50, y: currentY },
      data: {
        label: asset.asset_name || `Asset ${index + 1}`,
        assetType: asset.asset_type || 'unknown',
        currentOwner: 'Received',
        acquisition: 'Trade',
      },
    }
    branchNodes.push(receivedNode)
    
    // Connect initial asset to received asset
    branchEdges.push({
      id: `${initialAssetNode.id}-to-${receivedNodeId}`,
      source: initialAssetNode.id,
      target: receivedNodeId,
    })
    
    currentY += 80
  })
  
  // Process sub-branches recursively
  if (branch.sub_branches && branch.sub_branches.length > 0) {
    let subBranchX = xStart + 250
    
    branch.sub_branches.forEach((subBranch: any, subIndex: number) => {
      const subBranchId = `${branchId}-sub-${subIndex}`
      const { branchNodes: subNodes, branchEdges: subEdges, width: subWidth } = processBranchRecursively(
        subBranch,
        subBranchId,
        subBranchX,
        yStart + 150,
        depth + 1,
        baseNodeId + (subIndex + 1) * 100
      )
      
      branchNodes.push(...subNodes)
      branchEdges.push(...subEdges)
      
      // Connect some received asset to the sub-branch (simplified)
      if (receivedAssets.length > subIndex && subNodes.length > 0) {
        const sourceId = `${branchId}-received-${subIndex}`
        branchEdges.push({
          id: `${sourceId}-to-${subNodes[0].id}`,
          source: sourceId,
          target: subNodes[0].id,
          animated: true,
        })
      }
      
      subBranchX += subWidth + 100
      maxWidth = Math.max(maxWidth, subBranchX - xStart)
    })
  } else {
    // No sub-branches, show final outcomes
    branch.final_outcomes?.forEach((outcome: any, index: number) => {
      const outcomeNodeId = `${branchId}-outcome-${index}`
      const outcomeNode: Node = {
        id: outcomeNodeId,
        type: 'outcomeNode',
        position: { x: xStart + 250, y: yStart + index * 80 },
        data: {
          label: outcome.asset_name || `Final Asset ${index + 1}`,
          assetType: outcome.asset_type || 'unknown',
          currentOwner: outcome.current_owner || 'Unknown',
          acquisition: outcome.acquisition_method || 'Unknown',
          isCurrentOwner: true,
        },
      }
      branchNodes.push(outcomeNode)
      
      // Connect to received assets or initial asset
      const sourceId = receivedAssets.length > 0 
        ? `${branchId}-received-0` 
        : initialAssetNode.id
      
      branchEdges.push({
        id: `${sourceId}-to-${outcomeNodeId}`,
        source: sourceId,
        target: outcomeNodeId,
      })
    })
    
    maxWidth = Math.max(maxWidth, 450)
  }
  
  return { branchNodes, branchEdges, width: maxWidth }
}