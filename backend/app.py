from flask import Flask, request, jsonify
from flask_cors import CORS
from model_utils import (
    predict_game, 
    get_team_stats, 
    get_matchup_stats, 
    load_model_and_data, 
    TEAM_ABBREVIATIONS,
    predictor  # The GamePredictor instance
)
import pandas as pd
import os

app = Flask(__name__)

def initialize_app():
    """Initialize model and data"""
    if not load_model_and_data() or not predictor.load_model():
        print("⚠️ WARNING: Failed to initialize model or data")

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
    "allow_headers": ["Content-Type"],
    "supports_credentials": True
}})

TEAM_ABBREVIATION_MAP = {
    # Eastern Conference
    "ATL": "ATLANTA HAWKS",
    "BOS": "BOSTON CELTICS",
    "BKN": "BROOKLYN NETS",
    "CHA": "CHARLOTTE HORNETS",
    "CHI": "CHICAGO BULLS",
    "CLE": "CLEVELAND CAVALIERS",
    "DET": "DETROIT PISTONS",
    "IND": "INDIANA PACERS",
    "MIA": "MIAMI HEAT",
    "MIL": "MILWAUKEE BUCKS",
    "NYK": "NEW YORK KNICKS",
    "ORL": "ORLANDO MAGIC",
    "PHI": "PHILADELPHIA 76ERS",
    "TOR": "TORONTO RAPTORS",
    "WAS": "WASHINGTON WIZARDS",
    # Western Conference
    "DAL": "DALLAS MAVERICKS",
    "DEN": "DENVER NUGGETS",
    "GSW": "GOLDEN STATE WARRIORS",
    "HOU": "HOUSTON ROCKETS",
    "LAC": "LOS ANGELES CLIPPERS",
    "LAL": "LOS ANGELES LAKERS",
    "MEM": "MEMPHIS GRIZZLIES",
    "MIN": "MINNESOTA TIMBERWOLVES",
    "NOP": "NEW ORLEANS PELICANS",
    "OKC": "OKLAHOMA CITY THUNDER",
    "PHX": "PHOENIX SUNS",
    "POR": "PORTLAND TRAIL BLAZERS",
    "SAC": "SACRAMENTO KINGS",
    "SAS": "SAN ANTONIO SPURS",
    "UTA": "UTAH JAZZ"
}

# Dictionary to hold data for different seasons
season_data = {}

# Load data with proper column mapping and processing
try:
    # Map your actual column names to our expected names
    column_mapping = {
        'Home/Neutral': 'home_team',
        'Visitor/Neutral': 'visitor_team',
        'Home_PTS': 'home_pts',
        'Visitor_PTS': 'visitor_pts',
        'Wins (Home)': 'home_wins',
        'Losses (Home)': 'home_losses',
        'Wins (Visitor)': 'visitor_wins',
        'Losses (Visitor)': 'visitor_losses'
    }
    
    # Load each season's data with column renaming
    for season in ["2021-2022", "2022-2023", "2023-2024", "2024-2025"]:
        filename = f'data/nba_{season.replace("-", "_")}_final_data.csv'
        df = pd.read_csv(filename)
        
        # Clean team names - remove any whitespace and convert to uppercase
        df['Home/Neutral'] = df['Home/Neutral'].str.strip().str.upper()
        df['Visitor/Neutral'] = df['Visitor/Neutral'].str.strip().str.upper()
        
        # Rename columns
        df = df.rename(columns=column_mapping)
        
        # Add home_win column
        df['home_win'] = (df['home_pts'] > df['visitor_pts']).astype(int)
        
        season_data[season] = df
        
        # Debug print to verify data loading
        print(f"Loaded {season} data. Sample home teams:", df['home_team'].unique()[:5])
        
except Exception as e:
    print(f"Error loading data: {str(e)}")
    raise e  # Re-raise the error to see it in logs

#OPTIONS handler for preflight requests
@app.route('/api/<path:path>', methods=['OPTIONS'])
def options_handler(path):
    return {}, 200

@app.route('/api/predict-teams', methods=['POST'])
def predict_teams():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        home_team = data.get('home_team', '').upper()
        away_team = data.get('away_team', '').upper()
        
        if not home_team or not away_team:
            return jsonify({"error": "Missing team abbreviations"}), 400
        
        # Add debug logging
        print(f"Attempting prediction for {home_team} vs {away_team}")
        
        # Get team statistics
        home_stats = get_team_stats(home_team)
        away_stats = get_team_stats(away_team)
        matchup_stats = get_matchup_stats(home_team, away_team)
        
        if not home_stats or not away_stats:
            return jsonify({
                "error": "Could not fetch team stats",
                "details": f"Home stats: {bool(home_stats)}, Away stats: {bool(away_stats)}"
            }), 404
        
        # Make prediction using the predictor instance
        prediction_result = predictor.predict_game(home_stats, away_stats, matchup_stats)
        
        if not prediction_result:
            return jsonify({"error": "Prediction failed"}), 500
        
        # Get team names for response
        home_team_name = TEAM_ABBREVIATION_MAP.get(home_team, home_team)
        away_team_name = TEAM_ABBREVIATION_MAP.get(away_team, away_team)
        
        # Determine predicted winner name
        if prediction_result['prediction'] == 1:
            predicted_winner_name = home_team_name.title()
        else:
            predicted_winner_name = away_team_name.title()
        
        # Build comprehensive response
        response = {
            "prediction": prediction_result['prediction'],
            "home_win_prob": prediction_result['home_win_prob'],
            "away_win_prob": prediction_result['away_win_prob'],
            "predicted_winner": predicted_winner_name,
            "confidence": prediction_result['confidence'],
            "team_stats": {
                "home": {
                    **home_stats,
                    "team_name": home_team_name.title(),
                    "abbreviation": home_team
                },
                "away": {
                    **away_stats,
                    "team_name": away_team_name.title(),
                    "abbreviation": away_team
                }
            },
            "matchup_record": {
                "home_wins": matchup_stats.get('home_wins', 0),
                "away_wins": matchup_stats.get('away_wins', 0),
                "total_games": (matchup_stats.get('home_wins', 0) + 
                              matchup_stats.get('away_wins', 0))
            },
            "status": "success"
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Prediction failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "Prediction failed",
            "details": str(e)
        }), 500


@app.route("/api/compare-teams", methods=["GET"])
def compare_teams():
    team1_abbr = request.args.get("team1", "").strip().upper()
    team2_abbr = request.args.get("team2", "").strip().upper()
    season = request.args.get("season", "2024-2025")

    if not team1_abbr or not team2_abbr:
        return jsonify({"error": "Both team1 and team2 must be specified."}), 400

    # Convert abbreviations to full names if needed
    team1 = TEAM_ABBREVIATION_MAP.get(team1_abbr, team1_abbr)
    team2 = TEAM_ABBREVIATION_MAP.get(team2_abbr, team2_abbr)

    data = season_data.get(season)
    if data is None:
        return jsonify({"error": f"Data for season {season} not available."}), 400

    # Debug: Print the team names being searched
    print(f"Searching for teams: {team1} and {team2}")

    # Get team stats - more robust lookup
    def get_team_stats_comparison(team):
        home_games = data[data['home_team'] == team]
        visitor_games = data[data['visitor_team'] == team]
        
        if home_games.empty and visitor_games.empty:
            return None
            
        total_wins = (home_games['home_win'].sum() + 
                     (visitor_games['home_win'] == 0).sum())
        
        total_ppg = (home_games['home_pts'].sum() + 
                    visitor_games['visitor_pts'].sum()) / \
                   (len(home_games) + len(visitor_games)) if (len(home_games) + len(visitor_games)) > 0 else 0
        
        return {
            'wins': int(total_wins),
            'ppg': float(total_ppg)
        }

    stats1 = get_team_stats_comparison(team1)
    stats2 = get_team_stats_comparison(team2)

    if stats1 is None or stats2 is None:
        return jsonify({
            "error": "One or both teams not found.",
            "available_teams": {
                "home_teams": list(data['home_team'].unique()),
                "visitor_teams": list(data['visitor_team'].unique())
            }
        }), 404

    # Calculate head-to-head results
    head_to_head = calculate_head_to_head(data, team1, team2)

    return jsonify({
        team1_abbr: stats1,  # Return the original abbreviations in response
        team2_abbr: stats2,
        "headToHead": {
            team1_abbr: head_to_head[team1],
            team2_abbr: head_to_head[team2]
        }
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

@app.route('/api/health', methods=['GET'])
def health_check():
    """Enhanced health check endpoint"""
    try:
        model_loaded = bool(predictor.model)
        scaler_loaded = bool(predictor.scaler)
        data_loaded = bool(season_data)
        
        # Determine overall status
        if model_loaded and scaler_loaded and data_loaded:
            status = "healthy"
        elif model_loaded or data_loaded:
            status = "degraded"
        else:
            status = "unhealthy"
        
        return jsonify({
            'status': status,
            'services': {
                'model': model_loaded,
                'scaler': scaler_loaded,
                'data': data_loaded
            },
            'seasons_loaded': list(season_data.keys()) if season_data else [],
            'model_type': predictor.model.__class__.__name__ if predictor.model else None,
            'total_games': sum(len(df) for df in season_data.values()) if season_data else 0
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'services': {
                'model': False,
                'scaler': False,
                'data': False
            }
        }), 500

@app.route('/api/teams', methods=['GET'])
def get_teams():
    """Get team list with additional metadata"""
    teams = []
    for abbr, name in TEAM_ABBREVIATION_MAP.items():
        teams.append({
            'abbreviation': abbr,
            'name': name.title(),
            'conference': 'Eastern' if abbr in [
                'ATL', 'BOS', 'BKN', 'CHA', 'CHI', 
                'CLE', 'DET', 'IND', 'MIA', 'MIL',
                'NYK', 'ORL', 'PHI', 'TOR', 'WAS'
            ] else 'Western'
        })
    return jsonify({'teams': sorted(teams, key=lambda x: x['name'])})

# Initialize the application
print("🚀 Initializing The Bench Prophet...")
initialize_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)