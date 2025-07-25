import pandas as pd
import joblib
import os

# Team abbreviations dictionary
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

# Global variables
model = None
season_data = {}

def load_model_and_data():
    """Load the trained model and NBA data"""
    global model, season_data
    
    try:
        # Load the model
        if os.path.exists('model.pkl'):
            model = joblib.load('model.pkl')
            print("Model loaded successfully")
        else:
            print("Model file 'model.pkl' not found")
            return False
        
        # Load season data
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
        
        # Load each season's data
        for season in ["2021-2022", "2022-2023", "2023-2024", "2024-2025"]:
            filename = f'data/nba_{season.replace("-", "_")}_final_data.csv'
            if os.path.exists(filename):
                df = pd.read_csv(filename)
                
                # Clean team names
                df['Home/Neutral'] = df['Home/Neutral'].str.strip().str.upper()
                df['Visitor/Neutral'] = df['Visitor/Neutral'].str.strip().str.upper()
                
                # Rename columns
                df = df.rename(columns=column_mapping)
                
                # Add home_win column
                df['home_win'] = (df['home_pts'] > df['visitor_pts']).astype(int)
                
                season_data[season] = df
                print(f"Loaded {season} data: {len(df)} rows")
        
        # Try to load a single combined data file if no season files found
        if not season_data:
            data_files = ['nba_data.csv', 'data.csv', 'nba_games.csv', 'games.csv']
            for filename in data_files:
                if os.path.exists(filename):
                    df = pd.read_csv(filename)
                    # Clean team names if columns exist
                    if 'Home/Neutral' in df.columns:
                        df['Home/Neutral'] = df['Home/Neutral'].str.strip().str.upper()
                    if 'Visitor/Neutral' in df.columns:
                        df['Visitor/Neutral'] = df['Visitor/Neutral'].str.strip().str.upper()
                    
                    season_data['combined'] = df
                    print(f"Loaded combined data from {filename}: {len(df)} rows")
                    break
        
        if not season_data:
            print("No season data files found")
            return False
            
        return True
    except Exception as e:
        print(f"Error loading model/data: {str(e)}")
        return False

def get_combined_data():
    """Get combined data from all seasons"""
    if not season_data:
        return None
    
    if 'combined' in season_data:
        return season_data['combined']
    
    # Combine all season data
    all_data = []
    for season, df in season_data.items():
        all_data.append(df)
    
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    
    return None

def get_team_stats(team_abbr):
    """Get team statistics from the dataset"""
    try:
        data = get_combined_data()
        if data is None:
            return None
            
        team_name = TEAM_ABBREVIATIONS.get(team_abbr.upper(), team_abbr.upper())
        
        # Get games where team played as home
        team_home = data[data['Home/Neutral'] == team_name].copy()
        # Get games where team played as visitor
        team_away = data[data['Visitor/Neutral'] == team_name].copy()
        
        if 'Date' in data.columns:
            team_home = team_home.sort_values('Date', ascending=False)
            team_away = team_away.sort_values('Date', ascending=False)
            # Combine and get most recent games
            recent = pd.concat([team_home, team_away]).sort_values('Date', ascending=False)
        else:
            recent = pd.concat([team_home, team_away])
        
        if recent.empty:
            return None
        
        # Get the most recent game to extract current stats
        latest = recent.iloc[0]
        
        # Determine if team was home or away in latest game
        is_home = latest["Home/Neutral"] == team_name
        prefix = "Home" if is_home else "Visitor"
        
        # Extract stats with fallback values
        try:
            wins = int(latest[f"Wins ({prefix})"])
        except (KeyError, ValueError):
            wins = 0
            
        try:
            losses = int(latest[f"Losses ({prefix})"])
        except (KeyError, ValueError):
            losses = 0
            
        try:
            recent_win_pct = float(latest[f"Recent Win % ({prefix})"])
        except (KeyError, ValueError):
            recent_win_pct = 0.5  # Default to 50%
            
        try:
            recent_losses = int(latest[f"Recent Losses ({prefix})"])
        except (KeyError, ValueError):
            recent_losses = 0
        
        return {
            "wins": wins,
            "losses": losses,
            "recent_win_pct": recent_win_pct,
            "recent_losses": recent_losses
        }
    except Exception as e:
        print(f"Error getting team stats for {team_abbr}: {str(e)}")
        return None

def get_matchup_stats(home_team, away_team):
    """Get head-to-head matchup statistics"""
    try:
        data = get_combined_data()
        if data is None:
            return {"home_wins": 0, "away_wins": 0, "matchup_home_wins": 0, "matchup_away_wins": 0}
            
        home_name = TEAM_ABBREVIATIONS.get(home_team.upper(), home_team.upper())
        away_name = TEAM_ABBREVIATIONS.get(away_team.upper(), away_team.upper())
        
        # Find games between these two teams
        matchups = data[
            ((data['Home/Neutral'] == home_name) & (data['Visitor/Neutral'] == away_name)) |
            ((data['Home/Neutral'] == away_name) & (data['Visitor/Neutral'] == home_name))
        ]
        
        if 'Date' in data.columns:
            matchups = matchups.sort_values('Date', ascending=False)
        
        if matchups.empty:
            return {"home_wins": 0, "away_wins": 0, "matchup_home_wins": 0, "matchup_away_wins": 0}
        
        # Calculate wins when home_team was actually at home vs away_team
        home_wins = 0
        away_wins_as_visitor = 0
        away_wins = 0
        home_wins_vs_away = 0
        
        try:
            home_wins = len(matchups[
                (matchups['Home/Neutral'] == home_name) & 
                (matchups['Visitor/Neutral'] == away_name) &
                (matchups['Home_PTS'] > matchups['Visitor_PTS'])
            ])
            
            away_wins_as_visitor = len(matchups[
                (matchups['Home/Neutral'] == away_name) & 
                (matchups['Visitor/Neutral'] == home_name) &
                (matchups['Visitor_PTS'] > matchups['Home_PTS'])
            ])
            
            away_wins = len(matchups[
                (matchups['Home/Neutral'] == away_name) & 
                (matchups['Visitor/Neutral'] == home_name) &
                (matchups['Home_PTS'] > matchups['Visitor_PTS'])
            ])
            
            home_wins_vs_away = len(matchups[
                (matchups['Home/Neutral'] == home_name) & 
                (matchups['Visitor/Neutral'] == away_name) &
                (matchups['Visitor_PTS'] > matchups['Home_PTS'])
            ])
        except KeyError:
            # If PTS columns don't exist, return zeros
            pass
        
        total_home_wins = home_wins + away_wins_as_visitor
        total_away_wins = away_wins + home_wins_vs_away
        
        return {
            "home_wins": total_home_wins,
            "away_wins": total_away_wins,
            "matchup_home_wins": home_wins,
            "matchup_away_wins": away_wins
        }
    except Exception as e:
        print(f"Error getting matchup stats: {str(e)}")
        return {"home_wins": 0, "away_wins": 0, "matchup_home_wins": 0, "matchup_away_wins": 0}

def predict(features_dict):
    """Make prediction based on features dictionary"""
    try:
        if model is None:
            raise ValueError("Model not loaded")
        
        # Ensure all required features are present with default values
        required_features = [
            'Recent Win % (Home)', 'Recent Losses (Home)',
            'Recent Win % (Visitor)', 'Recent Losses (Visitor)',
            'Matchup Wins (Home)', 'Matchup Wins (Visitor)',
            'DSLG (Home)', 'DSLG (Visitor)',
            'Wins (Home)', 'Losses (Home)', 
            'Wins (Visitor)', 'Losses (Visitor)'
        ]
        
        # Fill in missing features with defaults
        complete_features = {}
        for feature in required_features:
            complete_features[feature] = features_dict.get(feature, 0)
        
        # Create DataFrame for prediction
        X = pd.DataFrame([complete_features])
        
        # Make prediction
        prediction = model.predict(X)[0]
        probabilities = model.predict_proba(X)[0]
        
        return {
            'prediction': int(prediction),
            'home_win_prob': float(probabilities[1]),  # Class 1 = home win
            'away_win_prob': float(probabilities[0]),  # Class 0 = away win
            'features': complete_features
        }
    except Exception as e:
        print(f"Error making prediction: {str(e)}")
        return None

def predict_game(home_team_stats, away_team_stats, matchup_stats):
    """Make prediction based on team stats"""
    try:
        # Prepare features for prediction
        features = {
            'Recent Win % (Home)': home_team_stats.get('recent_win_pct', 0.5),
            'Recent Losses (Home)': home_team_stats.get('recent_losses', 0),
            'Recent Win % (Visitor)': away_team_stats.get('recent_win_pct', 0.5),
            'Recent Losses (Visitor)': away_team_stats.get('recent_losses', 0),
            'Matchup Wins (Home)': matchup_stats.get('matchup_home_wins', 0),
            'Matchup Wins (Visitor)': matchup_stats.get('matchup_away_wins', 0),
            'DSLG (Home)': 0,  # Default value - you may need to calculate this
            'DSLG (Visitor)': 0,  # Default value - you may need to calculate this
            'Wins (Home)': home_team_stats.get('wins', 0),
            'Losses (Home)': home_team_stats.get('losses', 0),
            'Wins (Visitor)': away_team_stats.get('wins', 0),
            'Losses (Visitor)': away_team_stats.get('losses', 0)
        }
        
        return predict(features)
    except Exception as e:
        print(f"Error making game prediction: {str(e)}")
        return None

def is_model_loaded():
    """Check if model is loaded"""
    return model is not None

def is_data_loaded():
    """Check if data is loaded"""
    return len(season_data) > 0

def get_data_info():
    """Get information about loaded data"""
    if not season_data:
        return None
    
    total_rows = 0
    seasons_info = {}
    
    for season, df in season_data.items():
        seasons_info[season] = len(df)
        total_rows += len(df)
    
    return {
        'total_rows': total_rows,
        'seasons': seasons_info
    }

# Initialize on import
def initialize():
    """Initialize the model and data"""
    return load_model_and_data()

# Auto-initialize when module is imported
if __name__ != '__main__':
    initialize()