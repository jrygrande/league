# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Sleeper Fantasy Football League Explorer** - a FastAPI-based backend application that analyzes Sleeper fantasy football leagues to provide deep insights into manager performance, player transactions, and trade analysis.

### Core Purpose
- Track complete player lifecycle across leagues (drafts, trades, waivers)
- Analyze trade effectiveness and manager skill
- Provide transaction-based insights to settle "who's the best manager" debates

## Architecture

**Backend Only**: FastAPI application with clean service architecture
- **FastAPI**: Async web framework with automatic API documentation
- **SQLite Database**: Caching layer for Sleeper API responses (`sleeper_cache.db`)
- **httpx**: Async HTTP client for Sleeper API requests
- **Pydantic**: Data validation and serialization

### Directory Structure
```
backend/
├── main.py              # FastAPI app with route definitions
├── client.py            # Sleeper API client with caching
├── database.py          # SQLite database setup and connection
├── services/
│   └── sleeper_service.py  # Business logic and data processing
└── models/
    └── sleeper.py       # Pydantic models for API responses
```

## Common Development Commands

### Running the Application
```bash
# Install dependencies (in virtual environment)
pip install -r requirements.txt

# Start development server
uvicorn backend.main:app --reload

# Alternative with host/port specification
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing
```bash
# Run tests
pytest tests/

# Run specific test file
pytest tests/test_endpoints.py

# Run with verbose output
pytest -v
```

### Database Management
- Database is auto-created on startup via `lifespan` event in `main.py`
- Cache file: `sleeper_cache.db` (SQLite)
- Cache TTL: 7 days for API responses

## Key Implementation Patterns

### API Client Pattern
- All Sleeper API calls go through `backend/client.py`
- Generic `get()` function handles caching and error handling
- Returns `None` for 404s, raises exceptions for other HTTP errors
- Cache keys are based on full URL

### Service Layer
- `sleeper_service.py` contains all business logic
- Aggregates multiple API calls for complex analysis
- Uses `asyncio.gather()` for concurrent API requests
- Implements semaphore-based rate limiting where needed

### Data Models
- All API responses are validated through Pydantic models
- Models in `backend/models/sleeper.py` match Sleeper API structure
- Optional fields extensively used due to API inconsistencies

## Key Features Implemented

### Core Endpoints
- `/user/{username}` - Get user by username
- `/league/{league_id}/drafts` - Get league drafts
- `/league/{league_id}/rosters` - Get current rosters
- `/league/{league_id}/transactions/{week}` - Get weekly transactions
- `/league/{league_id}/history` - Get full league history via previous_league_id

### Advanced Analysis
- `/league/{league_id}/player/{player_id}/lifecycle` - Complete player transaction history
- `/league/{league_id}/roster/{roster_id}/analysis` - How each player was acquired
- `/analysis/league/{league_id}/player/{player_id}/since_transaction/{transaction_id}` - Player performance analysis
- `/analysis/league/{league_id}/player/{player_id}/stints` - Player performance by team stint

### Performance Optimization
- Concurrent API calls using `asyncio.gather()`
- SQLite caching prevents redundant API requests
- Semaphore limiting for heavy operations
- Week-by-week data fetching (weeks 1-18)

## Important Notes

### Sleeper API Specifics
- Player IDs are strings, not integers
- Transaction timestamps are in milliseconds (Unix)
- Some historical data may return 404 - handle gracefully
- Draft types include "snake", "auction", etc.
- Transaction types: "trade", "waiver", "free_agent"

### Error Handling
- 404 responses return `None` or empty lists
- Other HTTP errors are raised as exceptions
- Database connections are properly closed in `finally` blocks
- Missing data is handled with `Optional` types and default values

### Testing Setup
- Uses `TestClient` from FastAPI
- Test constants defined for real league/player/transaction IDs
- Focus on integration testing of endpoints

## Frontend Development (In Progress)

### Implementation Tracking
When working on the frontend implementation, **ALWAYS reference** the `FRONTEND_IMPLEMENTATION_PLAN.md` file for the complete roadmap and checklist.

#### Progress Tracking Pattern
1. **Use TodoWrite tool** to track active tasks from the implementation plan
2. **Check off items** in `FRONTEND_IMPLEMENTATION_PLAN.md` as they are completed
3. **Update phase status** (✅/❌) in the plan document
4. **Reference specific sections** when working on components

#### Current Implementation Phase
- **Phase 1**: Project Setup & Infrastructure
- **Active Branch**: `player-lineage-viz` 
- **Next Steps**: Initialize Next.js project, configure dependencies

#### Key Frontend Goals
- Username entry → League selection → Player search → Interactive visualization
- Technology stack: Next.js + TypeScript + shadcn/ui + TanStack Query + React Flow
- Mobile-responsive design with accessibility support

#### Implementation Rules
- **Always check** the plan document before starting new components
- **Update progress markers** in the plan as work is completed
- **Use TodoWrite** for session-specific task tracking
- **Follow the established patterns** from the technical framework