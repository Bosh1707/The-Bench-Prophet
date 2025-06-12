from flask import Flask, request, jsonify
from model_utils import predict, get_team_stats
import joblib
import pandas as pd

app = Flask(__name__)
model = joblib.load('model.pkl')

data = pd.read_csv('data/nba_2023_2024_final_data.csv')

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
    if not team1 or not team2:
        return jsonify({"error": "Both team1 and team2 must be specified."}), 400

    stats1 = get_team_stats(data, team1)
    stats2 = get_team_stats(data, team2)

    if stats1 is None or stats2 is None:
        return jsonify({"error": "One or both teams not found."}), 404

    return jsonify({
        team1: stats1,
        team2: stats2
    })

if __name__ == "__main__":
    app.run(debug=True)