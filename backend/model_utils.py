import pandas as pd
import joblib
import os

# Team abbreviations dictionary
TEAM_ABBREVIATIONS = {
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
    """Enhanced get_team_stats with better error handling and debugging"""
    try:
        # Debug logging
        print(f"🔍 Getting stats for {team_abbr} in season {season}")
        
        # Check if abbreviation exists
        if team_abbr not in TEAM_ABBREVIATIONS:
            print(f"❌ Team abbreviation {team_abbr} not found in TEAM_ABBREVIATIONS")
            available_abbrs = list(TEAM_ABBREVIATIONS.keys())
            print(f"Available abbreviations: {available_abbrs}")
            return None
            
        team_name = TEAM_ABBREVIATIONS[team_abbr]
        print(f"✅ Mapped {team_abbr} to {team_name}")
        
        # Check if season data exists
        if season not in season_data:
            print(f"❌ Season {season} not found in season_data")
            print(f"Available seasons: {list(season_data.keys())}")
            return None
            
        df = season_data[season]
        print(f"✅ Found season data with {len(df)} rows")
        
        # Debug: Show unique team names in data
        unique_home_teams = df['home_team'].unique()
        unique_visitor_teams = df['visitor_team'].unique()
        print(f"Sample home teams in data: {unique_home_teams[:5]}")
        print(f"Sample visitor teams in data: {unique_visitor_teams[:5]}")
        
        # Check if team exists in data
        home_games = df[df['home_team'] == team_name]
        away_games = df[df['visitor_team'] == team_name]
        
        print(f"Found {len(home_games)} home games and {len(away_games)} away games for {team_name}")
        
        if home_games.empty and away_games.empty:
            print(f"❌ No games found for {team_name}")
            # Try fuzzy matching
            all_teams = set(df['home_team'].unique()) | set(df['visitor_team'].unique())
            similar_teams = [t for t in all_teams if team_abbr in t or any(word in t for word in team_name.split())]
            print(f"Similar teams found: {similar_teams}")
            return None
            
        # Calculate stats
        home_wins = len(home_games[home_games['home_win'] == 1])
        away_wins = len(away_games[away_games['home_win'] == 0])
        total_wins = home_wins + away_wins
        
        home_losses = len(home_games[home_games['home_win'] == 0])
        away_losses = len(away_games[away_games['home_win'] == 1])
        total_losses = home_losses + away_losses
        
        total_games = len(home_games) + len(away_games)
        
        stats = {
            'wins': total_wins,
            'losses': total_losses,
            'games_played': total_games,
            'win_pct': total_wins / max(total_games, 1),
            'ppg': 0,
            'recent_win_pct': 0.5,  # Default for now
            'recent_losses': 0      # Default for now
        }
        
        # Calculate points per game
        if total_games > 0:
            total_points = home_games['home_pts'].sum() + away_games['visitor_pts'].sum()
            stats['ppg'] = round(total_points / total_games, 1)
            
        print(f"✅ Stats calculated: W-L: {total_wins}-{total_losses}, PPG: {stats['ppg']}")
        return stats
        
    except Exception as e:
        print(f"❌ Error getting stats for {team_abbr}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def get_matchup_stats(home_abbr, away_abbr, season):
    """Enhanced matchup stats with better debugging"""
    try:
        print(f"🔍 Getting matchup stats: {home_abbr} vs {away_abbr} in {season}")
        
        home_team = TEAM_ABBREVIATIONS.get(home_abbr)
        away_team = TEAM_ABBREVIATIONS.get(away_abbr)
        
        if not home_team or not away_team:
            print(f"❌ Team mapping failed: {home_abbr}->{home_team}, {away_abbr}->{away_team}")
            return {}
        
        df = season_data.get(season, pd.DataFrame())
        if df.empty:
            print(f"❌ No data for season {season}")
            return {}
            
        # Find head-to-head games
        matchups = df[
            ((df['home_team'] == home_team) & (df['visitor_team'] == away_team)) |
            ((df['home_team'] == away_team) & (df['visitor_team'] == home_team))
        ]
        
        print(f"Found {len(matchups)} head-to-head games")
        
        if matchups.empty:
            return {
                'home_wins': 0,
                'away_wins': 0,
                'total_games': 0
            }
            
        # Calculate wins for each team
        home_wins = 0
        away_wins = 0
        
        for _, row in matchups.iterrows():
            if row['home_team'] == home_team:
                # home_team is playing at home
                if row['home_win'] == 1:
                    home_wins += 1
                else:
                    away_wins += 1
            else:
                # home_team is playing away
                if row['home_win'] == 0:
                    home_wins += 1  # away team (home_team) won
                else:
                    away_wins += 1  # home team (away_team) won
        
        result = {
            'home_wins': home_wins,
            'away_wins': away_wins,
            'total_games': len(matchups)
        }
        
        print(f"✅ Matchup stats: {result}")
        return result
        
    except Exception as e:
        print(f"❌ Error getting matchup stats: {str(e)}")
        return {}

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