# API Development Plan

This document outlines the plan for developing the API endpoints needed to track player history, transactions, and drafts in a Sleeper fantasy football league.

## Phase 1: Core Data Endpoints

We will start by building the core endpoints needed to fetch the raw data from the Sleeper API.

### 1. Get League Drafts

*   **Endpoint:** `/league/{league_id}/drafts`
*   **Sleeper API:** `GET /v1/league/{league_id}/drafts`
*   **Description:** This endpoint will return a list of all drafts for a given league. This is a foundational piece for analyzing draft performance.

### 2. Get League Rosters

*   **Endpoint:** `/league/{league_id}/rosters`
*   **Sleeper API:** `GET /v1/league/{league_id}/rosters`
*   **Description:** This endpoint will return a list of all rosters in a league, including the players on each roster. This is essential for knowing which manager owns which players.

### 3. Get League Transactions

*   **Endpoint:** `/league/{league_id}/transactions/{week}`
*   **Sleeper API:** `GET /v1/league/{league_id}/transactions/{round}`
*   **Description:** This endpoint will return all transactions for a given week in a league. We will need to call this endpoint for every week of the season to get all transactions. This is the core of our trade analysis.

### 4. Get All Players

*   **Endpoint:** `/players`
*   **Sleeper API:** `GET /v1/players/nfl`
*   **Description:** This endpoint will fetch the entire NFL player database from Sleeper. This is a large JSON file that contains information about every player. We will need this to look up player details like name, position, and team. We will need to implement caching for this endpoint to avoid fetching it repeatedly.

## Phase 2: Historical Data and Analysis

Once we have the core data endpoints, we can build on top of them to create more advanced features.

### 5. Track League History

*   **Endpoint:** `/league/{league_id}/history`
*   **Sleeper API:** `GET /v1/league/{league_id}` (and then recursively on `previous_league_id`)
*   **Description:** This endpoint will traverse the `previous_league_id` field in the league object to get the entire history of a league. It will return a list of league objects, one for each season.

### 6. Player Stats and Analysis

*   **Endpoint:** `/analysis/trade` (or similar)
*   **Sleeper API:** `GET /v1/stats/nfl/{season}` and `GET /v1/projections/nfl/{season}`
*   **Description:** This is a more complex endpoint that will require more thought. It will likely take a transaction object as input and return an analysis of the trade, including the lifetime points and points per game for each player involved. This will require us to fetch historical stats and projections from the Sleeper API and then process them.

## Implementation Strategy

We will implement these endpoints one by one, starting with Phase 1. For each endpoint, we will:

1.  Add a new function to `backend/main.py`.
2.  Add a new route to the FastAPI application.
3.  Test the endpoint thoroughly.

We will continue to use `httpx` for making asynchronous requests to the Sleeper API.
