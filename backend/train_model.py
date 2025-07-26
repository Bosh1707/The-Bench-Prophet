import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score
import joblib
import os

def load_data():
    """Load data from season files"""
    seasons = ["2021-2022", "2022-2023", "2023-2024"]
    dfs = []
    for season in seasons:
        file = f"data/nba_{season.replace('-','_')}_final_data.csv"
        if os.path.exists(file):
            df = pd.read_csv(file)
            # Standardize column names
            df.columns = df.columns.str.strip().str.lower()
            df['season'] = season
            dfs.append(df)
    return pd.concat(dfs)

def create_features(df):
    """Create features from available columns"""
    # Ensure we have required columns
    required_cols = ['home_pts', 'visitor_pts', 'home/neutral', 'visitor/neutral']
    if not all(col in df.columns for col in required_cols):
        raise ValueError("Missing required columns in data")
    
    # Create target variable
    df['home_win'] = (df['home_pts'] > df['visitor_pts']).astype(int)
    
    # Calculate basic features
    features = []
    for _, row in df.iterrows():
        features.append({
            'home_ppg': row.get('home_pts', 0),
            'away_ppg': row.get('visitor_pts', 0),
            'point_diff': row.get('home_pts', 0) - row.get('visitor_pts', 0),
            'home_win': row['home_win']
        })
    
    return pd.DataFrame(features)

def train():
    print("Loading data...")
    df = load_data()
    
    print("Creating features...")
    features = create_features(df)
    
    X = features.drop('home_win', axis=1)
    y = features['home_win']
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    print("Training model...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=8,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train_scaled, y_train)
    
    # Evaluate
    X_test_scaled = scaler.transform(X_test)
    y_pred = model.predict(X_test_scaled)
    print(f"\nModel Performance:")
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.2f}")
    print(f"ROC AUC: {roc_auc_score(y_test, model.predict_proba(X_test_scaled)[:,1]):.2f}")
    
    # Save artifacts
    joblib.dump(model, 'model.pkl')
    joblib.dump(scaler, 'scaler.pkl')
    print("\nSaved model artifacts:")
    print(f"- model.pkl (Size: {os.path.getsize('model.pkl')/1024:.1f} KB)")
    print(f"- scaler.pkl (Size: {os.path.getsize('scaler.pkl')/1024:.1f} KB)")

if __name__ == "__main__":
    print("Starting model training...")
    try:
        train()
        print("Training completed successfully!")
    except Exception as e:
        print(f"Error during training: {str(e)}")