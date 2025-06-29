from flask import Flask, request, jsonify
from flask_cors import CORS
from model_utils import predict, get_team_stats
import joblib
import pandas as pd
import os

app = Flask(__name__)

ALLOWED_ORIGINS = [
    "https://the-bench-prophet.vercel.app",
    "https://the-bench-prophet-nauflqscz-joshuas-projects-517c4114.vercel.app",
    "http://localhost:3000",
    "http://localhost:3001"
]

# Apply CORS only to /api/* routes with full access
CORS(app, resources={r"/api/*": {
    "origins": ALLOWED_ORIGINS,
    "methods": ["GET", "POST", "OPTIONS"],
    "allow_headers": ["*"]
}})


model = joblib.load('model.pkl')

# Dictionary to hold data for different seasons
season_data = {
    "2021-2022": pd.read_csv('data/nba_2021_2022_final_data.csv'),
    "2022-2023": pd.read_csv('data/nba_2022_2023_final_data.csv'),
    "2023-2024": pd.read_csv('data/nba_2023_2024_final_data.csv'),
    "2024-2025": pd.read_csv('data/nba_2024_2025_final_data.csv')
}

@app.route("/api/predict", methods=["POST"])
def predict_outcome():
    data_json = request.get_json()
    prediction, probs = predict(model, data_json)
    return jsonify({
        "prediction": "Home Team Wins" if prediction == 1 else "Visitor Team Wins",
        "probabilities": {
            "home_win": probs[1],
            "visitor_win": probs[0]
        }
    })

@app.route("/api/compare-teams", methods=["GET"])
def compare_teams():
    team1 = request.args.get("team1")
    team2 = request.args.get("team2")
    season = request.args.get("season", "2024-2025")  # Default to current season
    
    if not team1 or not team2:
        return jsonify({"error": "Both team1 and team2 must be specified."}), 400

    # Get the appropriate dataset for the season
    data = season_data.get(season)
    if data is None:
        return jsonify({"error": f"Data for season {season} not available."}), 400

    stats1 = get_team_stats(data, team1)
    stats2 = get_team_stats(data, team2)

    if stats1 is None or stats2 is None:
        return jsonify({"error": "One or both teams not found."}), 404

    # Calculate head-to-head results
    head_to_head = calculate_head_to_head(data, team1, team2)

    return jsonify({
        team1: stats1,
        team2: stats2,
        "headToHead": head_to_head
    })

def calculate_head_to_head(data, team1, team2):
    """Calculate head-to-head matchups between two teams"""
    # Filter games where these two teams played each other
    matchups = data[
        ((data['home_team'] == team1) & (data['visitor_team'] == team2)) |
        ((data['home_team'] == team2) & (data['visitor_team'] == team1))
    ]
    
    team1_wins = 0
    team2_wins = 0
    
    for _, row in matchups.iterrows():
        if row['home_team'] == team1:
            if row['home_win'] == 1:
                team1_wins += 1
            else:
                team2_wins += 1
        else:
            if row['home_win'] == 1:
                team2_wins += 1
            else:
                team1_wins += 1
    
    return {
        team1: team1_wins,
        team2: team2_wins
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)