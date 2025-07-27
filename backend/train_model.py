import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os

def create_dummy_model():
    """Create a dummy model if no training data is available"""
    print("Creating dummy model with synthetic data...")
    
    # Generate synthetic training data
    np.random.seed(42)
    n_samples = 1000
    
    # Create features that somewhat represent real basketball stats
    features = {
        'home_win_pct': np.random.beta(2, 2, n_samples),  # Win percentages tend to cluster around 0.5
        'away_win_pct': np.random.beta(2, 2, n_samples),
        'home_recent_win_pct': np.random.beta(2, 2, n_samples),
        'away_recent_win_pct': np.random.beta(2, 2, n_samples),
        'home_wins': np.random.poisson(40, n_samples),
        'home_losses': np.random.poisson(35, n_samples),
        'away_wins': np.random.poisson(40, n_samples),
        'away_losses': np.random.poisson(35, n_samples),
        'home_recent_losses': np.random.poisson(3, n_samples),
        'away_recent_losses': np.random.poisson(3, n_samples),
        'matchup_home_wins': np.random.poisson(2, n_samples),
        'matchup_away_wins': np.random.poisson(2, n_samples),
    }
    
    df = pd.DataFrame(features)
    
    # Add derived features
    df['win_pct_diff'] = df['home_win_pct'] - df['away_win_pct']
    df['recent_win_pct_diff'] = df['home_recent_win_pct'] - df['away_recent_win_pct']
    df['matchup_total'] = df['matchup_home_wins'] + df['matchup_away_wins']
    df['games_diff'] = (df['home_wins'] + df['home_losses']) - (df['away_wins'] + df['away_losses'])
    df['recent_momentum'] = df['home_recent_win_pct'] - df['away_recent_win_pct']
    df['matchup_home_advantage'] = np.where(
        df['matchup_total'] > 0,
        df['matchup_home_wins'] / df['matchup_total'],
        0.5
    )
    
    # Create target variable with some logic (home team advantage + win percentage advantage)
    home_advantage = 0.1  # 10% home court advantage
    prob_home_win = (
        home_advantage + 
        0.3 * df['win_pct_diff'] + 
        0.2 * df['recent_win_pct_diff'] +
        0.1 * (df['matchup_home_advantage'] - 0.5)
    ).clip(0.1, 0.9)  # Keep probabilities reasonable
    
    # Generate binary outcomes based on probabilities
    df['home_win'] = np.random.binomial(1, prob_home_win)
    
    return df

def train_model():
    """Train the prediction model"""
    print("🤖 Training NBA prediction model...")
    
    # Try to load real data first
    df = None
    
    # Look for training data files
    possible_files = [
        'data/nba_2023_2024_final_data.csv',
        'data/nba_2022_2023_final_data.csv',
        'data/nba_2021_2022_final_data.csv',
        'nba_data.csv',
        'training_data.csv'
    ]
    
    for file_path in possible_files:
        if os.path.exists(file_path):
            try:
                print(f"Loading data from {file_path}")
                df = pd.read_csv(file_path)
                break
            except Exception as e:
                print(f"Failed to load {file_path}: {e}")
                continue
    
    # If no real data found, create dummy model
    if df is None:
        df = create_dummy_model()
    
    # Prepare features and target
    feature_columns = [
        'home_win_pct', 'away_win_pct', 'win_pct_diff',
        'home_recent_win_pct', 'away_recent_win_pct', 'recent_win_pct_diff',
        'home_wins', 'home_losses', 'away_wins', 'away_losses',
        'home_recent_losses', 'away_recent_losses',
        'matchup_home_wins', 'matchup_away_wins', 'matchup_total',
        'games_diff', 'recent_momentum', 'matchup_home_advantage'
    ]
    
    # Create missing columns with defaults
    for col in feature_columns:
        if col not in df.columns:
            df[col] = 0
    
    X = df[feature_columns].fillna(0)
    
    # Create target if it doesn't exist
    if 'home_win' not in df.columns:
        if 'Home_PTS' in df.columns and 'Visitor_PTS' in df.columns:
            y = (df['Home_PTS'] > df['Visitor_PTS']).astype(int)
        else:
            # Use dummy target
            y = df.get('home_win', np.random.binomial(1, 0.55, len(df)))
    else:
        y = df['home_win']
    
    print(f"Training with {len(X)} samples and {len(feature_columns)} features")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train model
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train_scaled, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test_scaled)
    y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
    
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\n📊 Model Performance:")
    print(f"Accuracy: {accuracy:.3f}")
    print(f"Home team win rate in test set: {y_test.mean():.3f}")
    print(f"Predicted home win rate: {y_pred.mean():.3f}")
    
    # Save model and scaler
    joblib.dump(model, 'model.pkl')
    joblib.dump(scaler, 'scaler.pkl')
    
    print(f"\n💾 Model saved:")
    print(f"- model.pkl ({os.path.getsize('model.pkl')/1024:.1f} KB)")
    print(f"- scaler.pkl ({os.path.getsize('scaler.pkl')/1024:.1f} KB)")
    
    # Show feature importance
    feature_importance = pd.DataFrame({
        'feature': feature_columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print(f"\n🎯 Top 10 Most Important Features:")
    for _, row in feature_importance.head(10).iterrows():
        print(f"  {row['feature']}: {row['importance']:.3f}")
    
    return model, scaler

if __name__ == "__main__":
    try:
        train_model()
        print("\n✅ Model training completed successfully!")
    except Exception as e:
        print(f"\n❌ Training failed: {str(e)}")
        import traceback
        traceback.print_exc()