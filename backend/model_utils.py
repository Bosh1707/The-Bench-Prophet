from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from sklearn.linear_model import LogisticRegression
import joblib
import os

app = Flask(__name__)
CORS(app)

# Your existing team abbreviations dictionary
TEAM_ABBREVIATIONS = {
    "ATL": "Atlanta Hawks",
    "BOS": "Boston Celtics",
    "BKN": "Brooklyn Nets",
    "CHA": "Charlotte Hornets",
    "CHI": "Chicago Bulls",
    "CLE": "Cleveland Cavaliers",
    "DAL": "Dallas Mavericks",
    "DEN": "Denver Nuggets",
    "DET": "Detroit Pistons",
    "GSW": "Golden State Warriors",
    "HOU": "Houston Rockets",
    "IND": "Indiana Pacers",
    "LAC": "Los Angeles Clippers",
    "LAL": "Los Angeles Lakers",
    "MEM": "Memphis Grizzlies",
    "MIA": "Miami Heat",
    "MIL": "Milwaukee Bucks",
    "MIN": "Minnesota Timberwolves",
    "NOP": "New Orleans Pelicans",
    "NYK": "New York Knicks",
    "OKC": "Oklahoma City Thunder",
    "ORL": "Orlando Magic",
    "PHI": "Philadelphia 76ers",
    "PHX": "Phoenix Suns",
    "POR": "Portland Trail Blazers",
    "SAC": "Sacramento Kings",
    "SAS": "San Antonio Spurs",
    "TOR": "Toronto Raptors",
    "UTA": "Utah Jazz",
    "WAS": "Washington Wizards"
}

# Global variables to store model and data
model = None
data = None

def load_model_and_data():
    """Load the trained model and NBA data"""
    global model, data
    
    try:
        # Load the model
        if os.path.exists('model.pkl'):
            model = joblib.load('model.pkl')
            print("Model loaded successfully")
        else:
            print("Model file 'model.pkl' not found")
            return False
        
        # Load the data - try different common file names
        data_files = ['nba_data.csv', 'data.csv', 'nba_games.csv', 'games.csv']
        data_loaded = False
        
        for file in data_files:
            if os.path.exists(file):
                data = pd.read_csv(file)
                print(f"Data loaded from {file}: {len(data)} rows")
                data_loaded = True
                break
        
        if not data_loaded:
            print("No data file found")
            return False
            
        return True
    except Exception as e:
        print(f"Error loading model/data: {str(e)}")
        return False

def get_team_stats(team_abbr):
    """Get team statistics from the dataset"""
    try:
        team_name = TEAM_ABBREVIATIONS.get(team_abbr.upper(), team_abbr)
        
        # Get games where team played as home
        team_home = data[data['Home/Neutral'] == team_name].sort_values('Date', ascending=False)
        # Get games where team played as visitor
        team_away = data[data['Visitor/Neutral'] == team_name].sort_values('Date', ascending=False)
        
        # Combine and get most recent games
        recent = pd.concat([team_home, team_away]).sort_values('Date', ascending=False)
        
        if recent.empty:
            return None
        
        # Get the most recent game to extract current stats
        latest = recent.iloc[0]
        
        # Determine if team was home or away in latest game
        is_home = latest["Home/Neutral"] == team_name
        prefix = "Home" if is_home else "Visitor"
        
        return {
            "wins": int(latest[f"Wins ({prefix})"]),
            "losses": int(latest[f"Losses ({prefix})"]),
            "recent_win_pct": float(latest[f"Recent Win % ({prefix})"]),
            "recent_losses": int(latest[f"Recent Losses ({prefix})"])
        }
    except Exception as e:
        print(f"Error getting team stats for {team_abbr}: {str(e)}")
        return None

def get_matchup_stats(home_team, away_team):
    """Get head-to-head matchup statistics"""
    try:
        home_name = TEAM_ABBREVIATIONS.get(home_team.upper(), home_team)
        away_name = TEAM_ABBREVIATIONS.get(away_team.upper(), away_team)
        
        # Find games between these two teams
        matchups = data[
            ((data['Home/Neutral'] == home_name) & (data['Visitor/Neutral'] == away_name)) |
            ((data['Home/Neutral'] == away_name) & (data['Visitor/Neutral'] == home_name))
        ].sort_values('Date', ascending=False)
        
        if matchups.empty:
            return {"home_wins": 0, "away_wins": 0}
        
        # Calculate wins when home_team was actually at home vs away_team
        home_wins = len(matchups[
            (matchups['Home/Neutral'] == home_name) & 
            (matchups['Visitor/Neutral'] == away_name) &
            (matchups['Home_PTS'] > matchups['Visitor_PTS'])
        ])
        
        # Calculate wins when home_team was away vs away_team at home
        away_wins_as_visitor = len(matchups[
            (matchups['Home/Neutral'] == away_name) & 
            (matchups['Visitor/Neutral'] == home_name) &
            (matchups['Visitor_PTS'] > matchups['Home_PTS'])
        ])
        
        # Calculate wins when away_team was actually at home vs home_team
        away_wins = len(matchups[
            (matchups['Home/Neutral'] == away_name) & 
            (matchups['Visitor/Neutral'] == home_name) &
            (matchups['Home_PTS'] > matchups['Visitor_PTS'])
        ])
        
        # Calculate wins when away_team was away vs home_team at home  
        home_wins_vs_away = len(matchups[
            (matchups['Home/Neutral'] == home_name) & 
            (matchups['Visitor/Neutral'] == away_name) &
            (matchups['Visitor_PTS'] > matchups['Home_PTS'])
        ])
        
        total_home_wins = home_wins + away_wins_as_visitor
        total_away_wins = away_wins + home_wins_vs_away
        
        return {
            "home_wins": total_home_wins,
            "away_wins": total_away_wins,
            "matchup_home_wins": home_wins,  # For model features
            "matchup_away_wins": away_wins   # For model features
        }
    except Exception as e:
        print(f"Error getting matchup stats: {str(e)}")
        return {"home_wins": 0, "away_wins": 0, "matchup_home_wins": 0, "matchup_away_wins": 0}

def predict_game(home_team_stats, away_team_stats, matchup_stats):
    """Make prediction based on team stats"""
    try:
        # Prepare features for prediction (matching your model's expected features)
        features = {
            'Recent Win % (Home)': home_team_stats.get('recent_win_pct', 0),
            'Recent Losses (Home)': home_team_stats.get('recent_losses', 0),
            'Recent Win % (Visitor)': away_team_stats.get('recent_win_pct', 0),
            'Recent Losses (Visitor)': away_team_stats.get('recent_losses', 0),
            'Matchup Wins (Home)': matchup_stats.get('matchup_home_wins', 0),
            'Matchup Wins (Visitor)': matchup_stats.get('matchup_away_wins', 0),
            'DSLG (Home)': 0,  # You may need to calculate this
            'DSLG (Visitor)': 0,  # You may need to calculate this
            'Wins (Home)': home_team_stats.get('wins', 0),
            'Losses (Home)': home_team_stats.get('losses', 0),
            'Wins (Visitor)': away_team_stats.get('wins', 0),
            'Losses (Visitor)': away_team_stats.get('losses', 0)
        }
        
        # Create DataFrame for prediction
        X = pd.DataFrame([features])
        
        # Make prediction
        prediction = model.predict(X)[0]
        probabilities = model.predict_proba(X)[0]
        
        return {
            'prediction': prediction,
            'home_win_prob': float(probabilities[1]),  # Class 1 = home win
            'away_win_prob': float(probabilities[0]),  # Class 0 = away win
            'features': features
        }
    except Exception as e:
        print(f"Error making prediction: {str(e)}")
        return None

@app.route('/api/predict-teams', methods=['POST'])
def predict_teams():
    """Endpoint to predict game outcome based on team selection"""
    try:
        data_received = request.get_json()
        home_team = data_received.get('home_team')
        away_team = data_received.get('away_team')
        
        # Validate input
        if not home_team or not away_team:
            return jsonify({'error': 'Both home_team and away_team are required'}), 400
        
        if home_team == away_team:
            return jsonify({'error': 'Teams must be different'}), 400
        
        if home_team not in TEAM_ABBREVIATIONS or away_team not in TEAM_ABBREVIATIONS:
            return jsonify({'error': 'Invalid team abbreviation'}), 400
        
        # Get team statistics
        home_stats = get_team_stats(home_team)
        away_stats = get_team_stats(away_team)
        
        if not home_stats:
            return jsonify({'error': f'No data found for {TEAM_ABBREVIATIONS[home_team]}'}), 400
        
        if not away_stats:
            return jsonify({'error': f'No data found for {TEAM_ABBREVIATIONS[away_team]}'}), 400
        
        # Get matchup statistics
        matchup_stats = get_matchup_stats(home_team, away_team)
        
        # Make prediction
        prediction_result = predict_game(home_stats, away_stats, matchup_stats)
        
        if not prediction_result:
            return jsonify({'error': 'Prediction failed'}), 500
        
        # Determine winner
        if prediction_result['prediction'] == 1:
            predicted_winner = TEAM_ABBREVIATIONS[home_team]
        else:
            predicted_winner = TEAM_ABBREVIATIONS[away_team]
        
        # Prepare response
        response = {
            'predicted_winner': predicted_winner,
            'home_win_prob': prediction_result['home_win_prob'],
            'away_win_prob': prediction_result['away_win_prob'],
            'team_stats': {
                'home': home_stats,
                'away': away_stats
            }
        }
        
        # Add matchup record if games exist
        if matchup_stats['home_wins'] > 0 or matchup_stats['away_wins'] > 0:
            response['matchup_record'] = {
                'home_wins': matchup_stats['home_wins'],
                'away_wins': matchup_stats['away_wins']
            }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Error in predict_teams: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/predict', methods=['POST'])
def predict_manual():
    """Your existing endpoint for manual feature input"""
    try:
        features = request.get_json()
        
        # Validate that all required features are present
        required_features = [
            'Recent Win % (Home)', 'Recent Losses (Home)',
            'Recent Win % (Visitor)', 'Recent Losses (Visitor)',
            'Matchup Wins (Home)', 'Matchup Wins (Visitor)',
            'DSLG (Home)', 'DSLG (Visitor)',
            'Wins (Home)', 'Losses (Home)', 
            'Wins (Visitor)', 'Losses (Visitor)'
        ]
        
        # Check if all features are provided
        for feature in required_features:
            if feature not in features:
                return jsonify({'error': f'Missing feature: {feature}'}), 400
        
        # Create DataFrame for prediction
        X = pd.DataFrame([features])
        
        # Make prediction
        prediction = model.predict(X)[0]
        probabilities = model.predict_proba(X)[0]
        
        # Prepare response
        if prediction == 1:
            result = "Home team wins"
        else:
            result = "Visitor team wins"
        
        response = {
            'prediction': result,
            'probabilities': {
                'home_win': float(probabilities[1]),
                'visitor_win': float(probabilities[0])
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Error in predict_manual: {str(e)}")
        return jsonify({'error': 'Prediction failed'}), 500

@app.route('/api/teams', methods=['GET'])
def get_teams():
    """Endpoint to get list of all teams"""
    teams = [{'abbreviation': abbr, 'name': name} for abbr, name in TEAM_ABBREVIATIONS.items()]
    return jsonify({'teams': teams})

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    status = {
        'status': 'healthy',
        'model_loaded': model is not None,
        'data_loaded': data is not None
    }
    
    if data is not None:
        status['data_rows'] = len(data)
    
    return jsonify(status)

@app.route('/api/team-stats/<team_abbr>', methods=['GET'])
def get_individual_team_stats(team_abbr):
    """Get statistics for a specific team"""
    try:
        if team_abbr.upper() not in TEAM_ABBREVIATIONS:
            return jsonify({'error': 'Invalid team abbreviation'}), 400
        
        stats = get_team_stats(team_abbr)
        if not stats:
            return jsonify({'error': f'No data found for {TEAM_ABBREVIATIONS[team_abbr.upper()]}'}), 404
        
        response = {
            'team': TEAM_ABBREVIATIONS[team_abbr.upper()],
            'abbreviation': team_abbr.upper(),
            'stats': stats
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Error getting team stats: {str(e)}")
        return jsonify({'error': 'Failed to get team stats'}), 500

if __name__ == '__main__':
    # Load model and data on startup
    if load_model_and_data():
        print("Server starting with model and data loaded successfully")
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("Failed to load model or data. Please check your files.")
        print("Required files:")
        print("- model.pkl (trained model)")
        print("- One of: nba_data.csv, data.csv, nba_games.csv, games.csv")
        exit(1)