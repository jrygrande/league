# Frontend Implementation Plan: Player Lineage Visualization

## Overview

This document outlines the step-by-step implementation plan for building a Next.js frontend that visualizes comprehensive asset chains (player trade lineages) from the Sleeper Fantasy Football backend API.

## User Experience Flow

1. **Username Entry**: User enters their Sleeper username
2. **League Selection**: System fetches and displays user's leagues in a dropdown
3. **Player Search**: User searches for a player with autocomplete functionality
4. **Visualization**: Interactive tree/graph showing how the player was acquired and all subsequent trades

## Technology Stack

- **Framework**: Next.js 14+ with TypeScript
- **UI Components**: shadcn/ui with Radix UI primitives
- **Styling**: Tailwind CSS
- **Data Fetching**: TanStack Query (React Query)
- **Visualization**: React Flow (for interactive node graphs)
- **Form Handling**: React Hook Form with Zod validation
- **Icons**: Lucide React

## Implementation Phases

### Phase 1: Project Setup & Infrastructure ✅ (100% Complete)

#### 1.1 Initialize Next.js Project
- [x] Create `frontend/` directory
- [x] Initialize Next.js with TypeScript: `npx create-next-app@latest`
- [x] Configure project with: TypeScript, Tailwind CSS, ESLint, App Router

#### 1.2 Install Core Dependencies
- [x] Install additional packages:
  - `@tanstack/react-query` - Data fetching and caching
  - `react-hook-form` + `@hookform/resolvers` - Form handling
  - `zod` - Schema validation
  - `axios` - HTTP client
  - `@xyflow/react` (React Flow) - Interactive diagrams
  - `lucide-react` - Icons
  - `cmdk` - Command palette for search
  - `class-variance-authority`, `clsx`, `tailwind-merge`, `tailwindcss-animate` - shadcn/ui dependencies
- [x] Complete shadcn/ui setup: `npx shadcn@latest init`

#### 1.3 Project Structure Setup
```
frontend/
├── app/
│   ├── globals.css
│   ├── layout.tsx
│   └── page.tsx
├── components/
│   ├── ui/           # shadcn/ui components (to be created)
│   ├── forms/        # Form components
│   ├── search/       # Search and autocomplete
│   └── visualization/ # Chart/graph components
├── lib/
│   ├── api.ts        # API client
│   ├── types.ts      # TypeScript interfaces
│   └── utils.ts      # Utility functions (shadcn/ui)
├── hooks/            # Custom React hooks
└── styles/           # Additional CSS if needed
```
- [x] Basic Next.js app structure created with TypeScript
- [x] Tailwind CSS configured and working
- [x] All major dependencies installed
- [x] Initial project files in place (src/app structure)
- [x] Create component directories and core files
- [x] Complete shadcn/ui initialization

#### 1.4 Configure Backend CORS
- [x] Add CORS middleware to FastAPI backend
- [x] Allow localhost:3000 for development
- [x] Update CORS to support localhost:3001 (alternate port)

### Phase 2: Core Components & API Integration ✅ (100% Complete)

#### 2.1 API Client Setup
- [x] Create API client with Axios
- [x] Define TypeScript interfaces for all API responses:
  - `User`
  - `League`
  - `Player`
  - `ComprehensiveAssetChain`
  - `AssetChainBranch`

#### 2.2 React Query Setup
- [x] Configure QueryClient with proper defaults
- [x] Create custom hooks:
  - `useUser(username)` - Fetch user by username
  - `useUserLeagues(userId, season)` - Fetch user's leagues
  - `usePlayerSearch(query)` - Search players with debouncing
  - `useAssetChain(leagueId, rosterId, assetId)` - Get comprehensive asset chain

#### 2.3 Basic Layout Components
- [x] `AppLayout` - Main application layout (via layout.tsx)
- [x] `Header` - Application header with title (integrated in layout)
- [x] `LoadingSpinner` - Reusable loading component (via Skeleton)
- [x] `ErrorMessage` - Error display component (via Alert)

### Phase 3: User Input Forms ✅ (100% Complete)

#### 3.1 Username Input Form
- [x] Create `UsernameForm` component using React Hook Form
- [x] Add validation with Zod schema
- [x] Show loading state while fetching user data
- [x] Display error if username not found

#### 3.2 League Selector
- [x] Create `LeagueSelector` component
- [x] Dropdown/select showing league name and season
- [x] Handle multiple seasons for the same league
- [x] Show league metadata (team count, scoring type, etc.)

#### 3.3 Player Search with Autocomplete
- [x] Create `PlayerSearch` component using cmdk
- [x] Implement debounced search (300ms delay)
- [x] Show player details in dropdown:
  - Player name
  - Position
  - Team
  - Profile image (if available)
- [x] Limit results to ~10 players
- [x] Handle empty states and loading

### Phase 4: Data Visualization ✅/❌

#### 4.1 Asset Chain Tree Component
- [ ] Create `AssetChainVisualization` component using React Flow
- [ ] Node types:
  - `PlayerNode` - Original player/pick
  - `TradeNode` - Trade transaction
  - `BranchNode` - Asset branch point
  - `OutcomeNode` - Final asset state

#### 4.2 Interactive Features
- [ ] Click to expand/collapse branches
- [ ] Hover to show additional details
- [ ] Zoom and pan functionality
- [ ] Minimap for large trees
- [ ] Different node colors for:
  - Original assets
  - Traded assets
  - Current ownership
  - Draft picks vs players

#### 4.3 Summary Panel
- [ ] Create `ChainSummary` component showing:
  - Original acquisition details
  - Total branches created
  - Final asset count
  - Key statistics

### Phase 5: Enhanced UI & UX ✅/❌

#### 5.1 shadcn/ui Components
- [x] Install and configure needed components:
  - [x] `Button`
  - [x] `Input`
  - [x] `Select`
  - [x] `Command` (for search)
  - [x] `Card`
  - [x] `Badge`
  - [x] `Skeleton` (loading states)
  - [x] `Alert` (errors)
  - [x] `Dialog` (modals)

#### 5.2 Responsive Design
- [ ] Ensure mobile-friendly layouts
- [ ] Proper responsive breakpoints
- [ ] Touch-friendly interactions

#### 5.3 Loading & Error States
- [x] Skeleton loading for all data fetching
- [x] Proper error boundaries (via React Query)
- [x] Retry mechanisms for failed requests
- [x] Empty states with helpful messaging

### Phase 6: Performance & Polish ✅/❌

#### 6.1 Performance Optimization
- [x] Implement proper React Query caching strategies
- [x] Lazy load visualization components (dynamic imports for devtools)
- [ ] Optimize large asset trees (virtualization if needed)
- [ ] Image lazy loading for player avatars

#### 6.2 Accessibility
- [ ] Proper ARIA labels
- [ ] Keyboard navigation support
- [ ] Screen reader friendly
- [ ] Color contrast compliance

#### 6.3 Developer Experience
- [x] Add proper TypeScript types for all props
- [ ] ESLint configuration
- [ ] Prettier for code formatting
- [ ] Component documentation

## API Endpoints to Integrate

### Required Endpoints
- `GET /user/{username}` - Get user by username
- `GET /user/{username}/leagues/{season}` - Get user's leagues
- `GET /players` - Get all players (for search)
- `GET /analysis/league/{league_id}/manager/{roster_id}/comprehensive_chain/{asset_id}` - Get asset chain

### Nice-to-Have Endpoints
- Player search endpoint with query parameter
- Roster info for better context
- League settings for additional metadata

## File Structure Checklist

### Core Files to Create
- [x] `frontend/components/forms/UsernameForm.tsx`
- [x] `frontend/components/forms/LeagueSelector.tsx`
- [x] `frontend/components/search/PlayerSearch.tsx`
- [ ] `frontend/components/visualization/AssetChainVisualization.tsx`
- [ ] `frontend/components/visualization/ChainSummary.tsx`
- [x] `frontend/lib/api.ts`
- [x] `frontend/lib/types.ts`
- [x] `frontend/hooks/useUser.ts`
- [x] `frontend/hooks/useUserLeagues.ts`
- [x] `frontend/hooks/usePlayerSearch.ts`
- [x] `frontend/hooks/useAssetChain.ts`
- [x] `frontend/hooks/useDebounce.ts`
- [x] `frontend/lib/providers.tsx`

## Testing Strategy

### Manual Testing ✅ (Completed)
- [x] **Build Testing**: Production build compiles successfully
- [x] **TypeScript Testing**: No type errors across all files  
- [x] **API Integration Testing**: Backend connectivity verified
- [x] **Component Testing**: All shadcn/ui components render correctly
- [x] **Hook Testing**: Custom React Query hooks function properly
- [x] **Test Page**: Comprehensive test interface created (`/test`)
- [x] **CORS Testing**: Frontend-backend communication working

### Unit Tests
- [ ] Component rendering tests
- [ ] API hook tests
- [ ] Utility function tests

### Integration Tests
- [ ] User flow tests
- [ ] API integration tests
- [ ] Visualization interaction tests

## Deployment Preparation

### Build Configuration
- [x] Optimize Next.js build settings
- [x] Configure environment variables (API base URL)
- [x] Set up proper API base URL handling

### Vercel Deployment
- [ ] Configure `vercel.json` if needed
- [ ] Set up environment variables in Vercel
- [ ] Test production build

## Progress Tracking

Use the TodoWrite tool to mark each phase item as completed when finished. Update this document as requirements evolve or new insights are discovered during implementation.

## Success Metrics

- [ ] User can successfully find their leagues
- [ ] Player search returns relevant results quickly
- [ ] Asset chain visualization loads and displays correctly
- [ ] Interactive features work smoothly
- [ ] Responsive design works on mobile and desktop
- [ ] Fast loading times (<2s for initial page load)