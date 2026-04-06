import os
import sys


BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app import app  # noqa: E402


def test_health_endpoint_is_healthy():
    client = app.test_client()
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.get_json()

    assert body["status"] == "healthy"
    assert body["services"]["model"] is True
    assert body["services"]["scaler"] is True
    assert body["services"]["data"] is True


def test_predict_teams_endpoint_returns_expected_payload_shape():
    client = app.test_client()

    payload = {
        "home_team": "LAL",
        "away_team": "BOS",
        "season": "2023-2024",
    }
    response = client.post("/api/predict-teams", json=payload)

    assert response.status_code == 200
    body = response.get_json()

    assert "meta" in body
    assert "prediction" in body
    assert "stats" in body

    prediction = body["prediction"]
    probs = prediction["probabilities"]

    assert "winner" in prediction
    assert "confidence" in prediction
    assert "home" in probs and "away" in probs

    home_prob = float(probs["home"])
    away_prob = float(probs["away"])

    assert 0.0 <= home_prob <= 100.0
    assert 0.0 <= away_prob <= 100.0
    assert abs((home_prob + away_prob) - 100.0) <= 0.2
