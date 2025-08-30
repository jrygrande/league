import httpx
import asyncio
import json

BASE_URL = "http://127.0.0.1:8000"
TEST_USERNAME = "some_username" # This user might not exist, but tests the endpoint
TEST_LEAGUE_ID = "1191596293294166016"
TEST_PLAYER_ID = "6803" # Brandon Aiyuk
TEST_ROSTER_ID = 1 # Assuming a default roster ID for a league
TEST_SEASON = "2023"
TEST_WEEK = 1
TEST_TRANSACTION_ID_X = "877585619352756224"
TEST_TRANSACTION_ID_Y = "1154488895422275584"

async def test_endpoint(client: httpx.AsyncClient, url: str, endpoint_name: str, expected_status: int = 200):
    print(f"\n--- Testing {endpoint_name} ---")
    print(f"URL: {url}")
    try:
        response = await client.get(url, timeout=30.0) # Increased timeout
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        if response.status_code != expected_status:
            print(f"ISSUE: Expected status {expected_status}, got {response.status_code}")
            return False
    except httpx.RequestError as e:
        print(f"ISSUE: Request failed: {e}")
        return False
    except json.JSONDecodeError:
        print(f"ISSUE: Could not decode JSON response: {response.text}")
        return False
    return True

async def main():
    await asyncio.sleep(5) # Give the server some time to start up
    async with httpx.AsyncClient() as client:
        # 1. / (read_root)
        await test_endpoint(client, f"{BASE_URL}/", "read_root")

        # 2. /user/{username} (get_user)
        await test_endpoint(client, f"{BASE_URL}/user/{TEST_USERNAME}", "get_user")

        # 3. /players (get_all_players)
        await test_endpoint(client, f"{BASE_URL}/players", "get_all_players")

        # 4. /league/{league_id}/drafts (get_league_drafts)
        await test_endpoint(client, f"{BASE_URL}/league/{TEST_LEAGUE_ID}/drafts", "get_league_drafts")

        # 5. /league/{league_id}/rosters (get_league_rosters)
        await test_endpoint(client, f"{BASE_URL}/league/{TEST_LEAGUE_ID}/rosters", "get_league_rosters")

        # 6. /league/{league_id}/transactions/{week} (get_league_transactions)
        await test_endpoint(client, f"{BASE_URL}/league/{TEST_LEAGUE_ID}/transactions/{TEST_WEEK}", "get_league_transactions")

        # 7. /league/{league_id}/matchups/{week} (get_league_matchups)
        await test_endpoint(client, f"{BASE_URL}/league/{TEST_LEAGUE_ID}/matchups/{TEST_WEEK}", "get_league_matchups")

        # 8. /user/{username}/leagues/{season} (get_leagues_for_user)
        await test_endpoint(client, f"{BASE_URL}/user/{TEST_USERNAME}/leagues/{TEST_SEASON}", "get_leagues_for_user")

        # 9. /league/{league_id}/history (get_league_history)
        await test_endpoint(client, f"{BASE_URL}/league/{TEST_LEAGUE_ID}/history", "get_league_history")

        # 10. /league/{league_id}/transactions (get_all_league_transactions)
        await test_endpoint(client, f"{BASE_URL}/league/{TEST_LEAGUE_ID}/transactions", "get_all_league_transactions")

        # 11. /stats/nfl/{season} (get_nfl_player_stats)
        await test_endpoint(client, f"{BASE_URL}/stats/nfl/{TEST_SEASON}", "get_nfl_player_stats")

        # 12. /player/{player_id}/aggregated_stats/{season} (get_player_aggregated_stats)
        await test_endpoint(client, f"{BASE_URL}/player/{TEST_PLAYER_ID}/aggregated_stats/{TEST_SEASON}", "get_player_aggregated_stats")

        # 13. /league/{league_id}/player/{player_id}/lifecycle (get_player_lifecycle)
        await test_endpoint(client, f"{BASE_URL}/league/{TEST_LEAGUE_ID}/player/{TEST_PLAYER_ID}/lifecycle", "get_player_lifecycle")

        # 14. /league/{league_id}/roster/{roster_id}/analysis (get_roster_analysis)
        # This endpoint requires a valid roster_id for the TEST_LEAGUE_ID.
        # For now, we'll use a placeholder and expect it might fail if the roster_id is invalid.
        await test_endpoint(client, f"{BASE_URL}/league/{TEST_LEAGUE_ID}/roster/{TEST_ROSTER_ID}/analysis", "get_roster_analysis")

        # 15. /analysis/league/{league_id}/player/{player_id}/since_transaction/{transaction_id}
        await test_endpoint(client, f"{BASE_URL}/analysis/league/{TEST_LEAGUE_ID}/player/{TEST_PLAYER_ID}/since_transaction/{TEST_TRANSACTION_ID_X}", "get_player_performance_since_transaction")

        # 16. /analysis/league/{league_id}/player/{player_id}/between_transactions/{transaction_id_x}/{transaction_id_y}
        await test_endpoint(client, f"{BASE_URL}/analysis/league/{TEST_LEAGUE_ID}/player/{TEST_PLAYER_ID}/between_transactions/{TEST_TRANSACTION_ID_X}/{TEST_TRANSACTION_ID_Y}", "get_player_performance_between_transactions")


if __name__ == "__main__":
    asyncio.run(main())
