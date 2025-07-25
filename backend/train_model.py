import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os

# Configuration
DATA_DIR = 'data'
MODEL_FILE = 'model.pkl'
SEASONS = ["2021-2022", "2022-2023", "2023-2024", "2024-2025"]  # Use past seasons for training

def load_and_preprocess_data():
    """Load and preprocess data from multiple seasons"""
    all_data = []
    
    for season in SEASONS:
        filename = os.path.join(DATA_DIR, f'nba_{season.replace("-", "_")}_final_data.csv')
        if os.path.exists(filename):
            df = pd.read_csv(filename)
            
            # Clean and standardize team names
            df['Home/Neutral'] = df['Home/Neutral'].str.strip().str.upper()
            df['Visitor/Neutral'] = df['Visitor/Neutral'].str.strip().str.upper()
            
            # Create target variable (home team win = 1, loss = 0)
            df['home_win'] = (df['Home_PTS'] > df['Visitor_PTS']).astype(int)
            
            all_data.append(df)
    
    if not all_data:
        raise ValueError("No data files found")
    
    return pd.concat(all_data, ignore_index=True)

def create_features(df):
    """Create features for the model"""
    # Calculate rolling statistics for each team
    features = []
    
    for _, row in df.iterrows():
        home_team = row['Home/Neutral']
        away_team = row['Visitor/Neutral']
        date = row['Date']
        
        # Get home team stats
        home_team_games = df[((df['Home/Neutral'] == home_team) | 
                             (df['Visitor/Neutral'] == home_team)) & 
                            (df['Date'] < date)].sort_values('Date', ascending=False)
        
        # Get away team stats
        away_team_games = df[((df['Home/Neutral'] == away_team) | 
                             (df['Visitor/Neutral'] == away_team)) & 
                            (df['Date'] < date)].sort_values('Date', ascending=False)
        
        # Calculate features
        home_recent_win_pct = home_team_games.head(10)['home_win'].mean() if not home_team_games.empty else 0.5
        away_recent_win_pct = away_team_games.head(10)['home_win'].mean() if not away_team_games.empty else 0.5
        
        home_recent_losses = len(home_team_games.head(10)[home_team_games['home_win'] == 0])
        away_recent_losses = len(away_team_games.head(10)[away_team_games['home_win'] == 0])
        
        # Head-to-head matchups
        matchups = df[(((df['Home/Neutral'] == home_team) & (df['Visitor/Neutral'] == away_team)) |
                      ((df['Home/Neutral'] == away_team) & (df['Visitor/Neutral'] == home_team))) &
                     (df['Date'] < date)]
        
        home_wins_vs_away = len(matchups[(matchups['Home/Neutral'] == home_team) & (matchups['home_win'] == 1)]) + \
                           len(matchups[(matchups['Visitor/Neutral'] == home_team) & (matchups['home_win'] == 0)])
        
        away_wins_vs_home = len(matchups) - home_wins_vs_away if len(matchups) > 0 else 0
        
        # Season-to-date stats
        home_wins = row.get('Wins (Home)', 0)
        home_losses = row.get('Losses (Home)', 0)
        away_wins = row.get('Wins (Visitor)', 0)
        away_losses = row.get('Losses (Visitor)', 0)
        
        features.append({
            'Recent Win % (Home)': home_recent_win_pct,
            'Recent Losses (Home)': home_recent_losses,
            'Recent Win % (Visitor)': away_recent_win_pct,
            'Recent Losses (Visitor)': away_recent_losses,
            'Matchup Wins (Home)': home_wins_vs_away,
            'Matchup Wins (Visitor)': away_wins_vs_home,
            'DSLG (Home)': 0,  # Placeholder - you'd calculate defensive stats
            'DSLG (Visitor)': 0,  # Placeholder
            'Wins (Home)': home_wins,
            'Losses (Home)': home_losses,
            'Wins (Visitor)': away_wins,
            'Losses (Visitor)': away_losses,
            'home_win': row['home_win']
        })
    
    return pd.DataFrame(features)

def train_model(X_train, y_train):
    """Train the Random Forest model"""
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        random_state=42,
        class_weight='balanced'
    )
    
    model.fit(X_train, y_train)
    return model

def evaluate_model(model, X_test, y_test):
    """Evaluate model performance"""
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    
    print("Accuracy:", accuracy_score(y_test, y_pred))
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    return {
        'accuracy': accuracy_score(y_test, y_pred),
        'report': classification_report(y_test, y_pred, output_dict=True)
    }

def save_model(model, filename):
    """Save the trained model to disk"""
    joblib.dump(model, filename)
    print(f"Model saved to {filename}")

def main():
    # Load and preprocess data
    print("Loading and preprocessing data...")
    df = load_and_preprocess_data()
    
    # Create features
    print("Creating features...")
    feature_df = create_features(df)
    
    # Split into features and target
    X = feature_df.drop('home_win', axis=1)
    y = feature_df['home_win']
    
    # Split into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Train model
    print("Training model...")
    model = train_model(X_train, y_train)
    
    # Evaluate model
    print("Evaluating model...")
    evaluation = evaluate_model(model, X_test, y_test)
    
    # Save model
    save_model(model, MODEL_FILE)
    
    print("Training completed successfully!")

if __name__ == "__main__":
    main()