import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

LEAGUE_ID = "1191596293294166016"
PLAYER_ID = "6803"
TRANSACTION_ID_X = "1154488895422275584"
TRANSACTION_ID_Y = "877585619352756224"

def test_get_player_performance_between_transactions():
    response = client.get(f"/analysis/league/{LEAGUE_ID}/player/{PLAYER_ID}/between_transactions/{TRANSACTION_ID_X}/{TRANSACTION_ID_Y}")
    assert response.status_code == 200
    data = response.json()
    assert data["player_id"] == PLAYER_ID
    assert data["transaction_id_x"] == TRANSACTION_ID_X
    assert data["transaction_id_y"] == TRANSACTION_ID_Y
    assert "summary" in data
