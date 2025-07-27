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

class GamePredictor:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_names = None
    
    def load_model(self, model_path='model.pkl', scaler_path='scaler.pkl'):
        try:
            self.model = joblib.load(model_path)
            self.scaler = joblib.load(scaler_path)
            print("✅ Model and scaler loaded successfully")
            return True
        except Exception as e:
            print(f"❌ Error loading model/scaler: {str(e)}")
            return False
    
    def prepare_features(self, home_stats, away_stats, matchup_stats):
        """Enhanced feature engineering"""
        features = {
            # Win percentages
            'home_win_pct': home_stats['wins'] / (home_stats['wins'] + home_stats['losses'] + 1e-6),
            'away_win_pct': away_stats['wins'] / (away_stats['wins'] + away_stats['losses'] + 1e-6),
            'win_pct_diff': 0,  # Calculated below
            
            # Recent performance
            'home_recent_win_pct': home_stats.get('recent_win_pct', 0.5),
            'away_recent_win_pct': away_stats.get('recent_win_pct', 0.5),
            
            # Matchup history
            'matchup_ratio': (matchup_stats.get('matchup_home_wins', 0) + 1) / 
                           (matchup_stats.get('matchup_away_wins', 0) + 1),
            
            # Derived features
            'momentum_diff': (home_stats.get('recent_win_pct', 0.5) - 
                            away_stats.get('recent_win_pct', 0.5)),
            
            # Add your existing features
            'Recent Win % (Home)': home_stats.get('recent_win_pct', 0.5),
            'Recent Losses (Home)': home_stats.get('recent_losses', 0),
            # ... (keep your other feature mappings)
        }
        
        # Calculate derived features
        features['win_pct_diff'] = features['home_win_pct'] - features['away_win_pct']
        
        return pd.DataFrame([features])
    
    def predict_game(self, home_stats, away_stats, matchup_stats):
        """
        Main prediction method for the GamePredictor class
        """
        try:
            if not self.model or not self.scaler:
                raise ValueError("Model or scaler not loaded")
            
            # Prepare features for prediction
            features_df = self.prepare_features(home_stats, away_stats, matchup_stats)
            
            # Scale features
            features_scaled = self.scaler.transform(features_df)
            
            # Make prediction
            prediction = self.model.predict(features_scaled)[0]
            probabilities = self.model.predict_proba(features_scaled)[0]
            
            # Extract probabilities (assuming binary classification: 0=away win, 1=home win)
            away_win_prob = probabilities[0]
            home_win_prob = probabilities[1]
            
            # Determine winner
            predicted_winner = "home" if prediction == 1 else "away"
            
            return {
                'prediction': int(prediction),
                'home_win_prob': float(home_win_prob),
                'away_win_prob': float(away_win_prob),
                'predicted_winner': predicted_winner,
                'confidence': float(max(home_win_prob, away_win_prob))
            }
            
        except Exception as e:
            print(f"Prediction error: {str(e)}")
            return None

    def prepare_features(self, home_stats, away_stats, matchup_stats):
        """
        Prepare features for model input - updated to match your training data
        """
        try:
            # Calculate win percentages with small epsilon to avoid division by zero
            home_total_games = home_stats.get('wins', 0) + home_stats.get('losses', 0)
            away_total_games = away_stats.get('wins', 0) + away_stats.get('losses', 0)
            
            home_win_pct = home_stats.get('wins', 0) / max(home_total_games, 1)
            away_win_pct = away_stats.get('wins', 0) / max(away_total_games, 1)
            
            # Create feature dictionary matching your training data structure
            features = {
                # Basic win percentages
                'home_win_pct': home_win_pct,
                'away_win_pct': away_win_pct,
                'win_pct_diff': home_win_pct - away_win_pct,
                
                # Recent performance
                'home_recent_win_pct': home_stats.get('recent_win_pct', 0.5),
                'away_recent_win_pct': away_stats.get('recent_win_pct', 0.5),
                'recent_win_pct_diff': (home_stats.get('recent_win_pct', 0.5) - 
                                    away_stats.get('recent_win_pct', 0.5)),
                
                # Team records
                'home_wins': home_stats.get('wins', 0),
                'home_losses': home_stats.get('losses', 0),
                'away_wins': away_stats.get('wins', 0),
                'away_losses': away_stats.get('losses', 0),
                
                # Recent losses
                'home_recent_losses': home_stats.get('recent_losses', 0),
                'away_recent_losses': away_stats.get('recent_losses', 0),
                
                # Matchup statistics
                'matchup_home_wins': matchup_stats.get('home_wins', 0),
                'matchup_away_wins': matchup_stats.get('away_wins', 0),
                'matchup_total': (matchup_stats.get('home_wins', 0) + 
                                matchup_stats.get('away_wins', 0)),
                
                # Additional derived features
                'games_diff': home_total_games - away_total_games,
                'recent_momentum': (home_stats.get('recent_win_pct', 0.5) - 
                                away_stats.get('recent_win_pct', 0.5)),
            }
            
            # Handle case where no matchup history exists
            if features['matchup_total'] > 0:
                features['matchup_home_advantage'] = (features['matchup_home_wins'] / 
                                                    features['matchup_total'])
            else:
                features['matchup_home_advantage'] = 0.5  # Neutral
            
            return pd.DataFrame([features])
            
        except Exception as e:
            print(f"Feature preparation error: {str(e)}")
            # Return default features if there's an error
            default_features = {
                'home_win_pct': 0.5, 'away_win_pct': 0.5, 'win_pct_diff': 0,
                'home_recent_win_pct': 0.5, 'away_recent_win_pct': 0.5,
                'recent_win_pct_diff': 0, 'home_wins': 0, 'home_losses': 0,
                'away_wins': 0, 'away_losses': 0, 'home_recent_losses': 0,
                'away_recent_losses': 0, 'matchup_home_wins': 0,
                'matchup_away_wins': 0, 'matchup_total': 0, 'games_diff': 0,
                'recent_momentum': 0, 'matchup_home_advantage': 0.5
            }
            return pd.DataFrame([default_features])
    
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

def get_team_stats(team_abbr, season):
    """Get stats with fallbacks for missing data"""
    try:
        team_name = TEAM_ABBREVIATIONS.get(team_abbr)
        if not team_name:
            return None
            
        df = season_data.get(season)
        if df is None:
            return None
            
        home = df[df['home_team'] == team_name]
        away = df[df['visitor_team'] == team_name]
        
        if home.empty and away.empty:
            return None
            
        stats = {
            'wins': len(home[home['home_win']]) + len(away[~away['home_win']]),
            'losses': len(home[~home['home_win']]) + len(away[away['home_win']]),
            'ppg': 0,
            'last_5': []
        }
        
        # Calculate points per game
        total_games = len(home) + len(away)
        if total_games > 0:
            stats['ppg'] = round(
                (home['home_pts'].sum() + away['visitor_pts'].sum()) / total_games, 
                1
            )
            
        return stats
        
    except Exception as e:
        print(f"Error getting stats for {team_abbr}: {str(e)}")
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

# Initialize predictor instance
predictor = GamePredictor()

def predict(features_dict):
    """Legacy prediction function - maintain for backward compatibility"""
    try:
        if not predictor.model:
            raise ValueError("Model not loaded")
        
        # Convert legacy features to new format
        home_stats = {
            'wins': features_dict.get('Wins (Home)', 0),
            'losses': features_dict.get('Losses (Home)', 0),
            'recent_win_pct': features_dict.get('Recent Win % (Home)', 0.5),
            'recent_losses': features_dict.get('Recent Losses (Home)', 0)
        }
        
        away_stats = {
            'wins': features_dict.get('Wins (Visitor)', 0),
            'losses': features_dict.get('Losses (Visitor)', 0),
            'recent_win_pct': features_dict.get('Recent Win % (Visitor)', 0.5),
            'recent_losses': features_dict.get('Recent Losses (Visitor)', 0)
        }
        
        matchup_stats = {
            'matchup_home_wins': features_dict.get('Matchup Wins (Home)', 0),
            'matchup_away_wins': features_dict.get('Matchup Wins (Visitor)', 0)
        }
        
        # Use the enhanced predictor
        result = predictor.predict_game(home_stats, away_stats, matchup_stats)
        
        # Maintain legacy return format
        if result:
            return {
                'prediction': result['prediction'],
                'home_win_prob': result['home_win_prob'],
                'away_win_prob': result['away_win_prob'],
                'features': features_dict  # Preserve original features
            }
        return None
        
    except Exception as e:
        print(f"Legacy prediction error: {str(e)}")
        return None

def predict_game(home_team_stats, away_team_stats, matchup_stats):
    """Enhanced prediction function using GamePredictor"""
    try:
        # Use the predictor instance
        result = predictor.predict_game(home_team_stats, away_team_stats, matchup_stats)
        
        # Add team info to results
        if result:
            result['team_info'] = {
                'home': home_team_stats,
                'away': away_team_stats
            }
        return result
        
    except Exception as e:
        print(f"Game prediction error: {str(e)}")
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

def initialize():
    """Initialize model and data"""
    data_loaded = load_model_and_data()
    model_loaded = predictor.load_model()
    
    return {
        'data_loaded': data_loaded,
        'model_loaded': model_loaded,
        'status': 'ready' if (data_loaded and model_loaded) else 'error'
    }

# Auto-initialize
if __name__ != '__main__':
    initialize()