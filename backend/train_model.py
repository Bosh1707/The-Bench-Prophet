import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.model_selection import StratifiedKFold, GridSearchCV
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss, brier_score_loss
import joblib
import os
import glob
import re
import json
from datetime import datetime

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


def _resolve_training_files(base_dir):
    """Find all season CSV files in backend/data and return sorted paths."""
    data_dir = os.path.join(base_dir, 'data')
    season_files = sorted(glob.glob(os.path.join(data_dir, 'nba_*_final_data.csv')))
    return season_files


def _extract_season_from_path(file_path):
    """Extract season token like 2023-2024 from a file path."""
    match = re.search(r'nba_(\d{4})_(\d{4})_final_data\.csv$', os.path.basename(file_path))
    if not match:
        return None
    return f"{match.group(1)}-{match.group(2)}"


def _coalesce_columns(df, candidates, default=0):
    """Return first matching column from candidates, otherwise a default-filled series."""
    for col in candidates:
        if col in df.columns:
            return pd.to_numeric(df[col], errors='coerce')
    return pd.Series(default, index=df.index, dtype='float64')


def build_training_dataset(df):
    """Build model features in the exact schema expected by backend/model_utils.py."""
    home_wins = _coalesce_columns(df, ['home_wins', 'Wins (Home)'], default=0)
    home_losses = _coalesce_columns(df, ['home_losses', 'Losses (Home)'], default=0)
    away_wins = _coalesce_columns(df, ['away_wins', 'Wins (Visitor)', 'visitor_wins'], default=0)
    away_losses = _coalesce_columns(df, ['away_losses', 'Losses (Visitor)', 'visitor_losses'], default=0)

    home_recent_win_pct = _coalesce_columns(df, ['home_recent_win_pct', 'Recent Win % (Home)'], default=np.nan)
    away_recent_win_pct = _coalesce_columns(df, ['away_recent_win_pct', 'Recent Win % (Visitor)'], default=np.nan)

    home_recent_losses = _coalesce_columns(df, ['home_recent_losses', 'Recent Losses (Home)'], default=0)
    away_recent_losses = _coalesce_columns(df, ['away_recent_losses', 'Recent Losses (Visitor)'], default=0)

    matchup_home_wins = _coalesce_columns(df, ['matchup_home_wins', 'Matchup Wins (Home)'], default=0)
    matchup_away_wins = _coalesce_columns(df, ['matchup_away_wins', 'Matchup Wins (Visitor)'], default=0)

    home_games = home_wins + home_losses
    away_games = away_wins + away_losses

    home_win_pct = home_wins / np.maximum(home_games, 1)
    away_win_pct = away_wins / np.maximum(away_games, 1)

    # If recent win% is not present in source data, fall back to season win%.
    home_recent_win_pct = home_recent_win_pct.fillna(home_win_pct)
    away_recent_win_pct = away_recent_win_pct.fillna(away_win_pct)

    matchup_total = matchup_home_wins + matchup_away_wins
    matchup_home_advantage = np.where(
        matchup_total > 0,
        matchup_home_wins / np.maximum(matchup_total, 1),
        0.5
    )

    X = pd.DataFrame({
        'home_win_pct': home_win_pct,
        'away_win_pct': away_win_pct,
        'win_pct_diff': home_win_pct - away_win_pct,
        'home_recent_win_pct': home_recent_win_pct,
        'away_recent_win_pct': away_recent_win_pct,
        'recent_win_pct_diff': home_recent_win_pct - away_recent_win_pct,
        'home_wins': home_wins,
        'home_losses': home_losses,
        'away_wins': away_wins,
        'away_losses': away_losses,
        'home_recent_losses': home_recent_losses,
        'away_recent_losses': away_recent_losses,
        'matchup_home_wins': matchup_home_wins,
        'matchup_away_wins': matchup_away_wins,
        'matchup_total': matchup_total,
        'games_diff': home_games - away_games,
        'recent_momentum': home_recent_win_pct - away_recent_win_pct,
        'matchup_home_advantage': matchup_home_advantage,
    }).fillna(0)

    # Derive binary label if not already present.
    if 'home_win' in df.columns:
        y = pd.to_numeric(df['home_win'], errors='coerce').fillna(0).astype(int)
    elif 'Home_PTS' in df.columns and 'Visitor_PTS' in df.columns:
        y = (pd.to_numeric(df['Home_PTS'], errors='coerce').fillna(0) >
             pd.to_numeric(df['Visitor_PTS'], errors='coerce').fillna(0)).astype(int)
    elif 'home_pts' in df.columns and 'visitor_pts' in df.columns:
        y = (pd.to_numeric(df['home_pts'], errors='coerce').fillna(0) >
             pd.to_numeric(df['visitor_pts'], errors='coerce').fillna(0)).astype(int)
    else:
        # Last resort for malformed data: use a baseline home-court prior.
        y = pd.Series(np.random.binomial(1, 0.55, len(df)), index=df.index)

    return X, y


def _print_metrics(title, y_true, y_pred, y_prob):
    """Print consistent evaluation metrics for any split."""
    accuracy = accuracy_score(y_true, y_pred)
    auc = roc_auc_score(y_true, y_prob)
    loss = log_loss(y_true, y_prob)
    brier = brier_score_loss(y_true, y_prob)

    print(f"\n📊 {title}")
    print(f"Accuracy: {accuracy:.3f}")
    print(f"ROC-AUC: {auc:.3f}")
    print(f"Log Loss: {loss:.3f}")
    print(f"Brier Score: {brier:.3f}")

    return {
        'accuracy': float(round(accuracy, 6)),
        'roc_auc': float(round(auc, 6)),
        'log_loss': float(round(loss, 6)),
        'brier_score': float(round(brier, 6)),
        'home_win_rate_actual': float(round(float(np.mean(y_true)), 6)),
        'home_win_rate_predicted': float(round(float(np.mean(y_pred)), 6)),
    }

def train_model():
    """Train the prediction model"""
    print("🤖 Training NBA prediction model...")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    season_files = _resolve_training_files(base_dir)

    # Load and concatenate all available real seasons for broader generalization.
    df = None
    if season_files:
        frames = []
        for file_path in season_files:
            try:
                print(f"Loading data from {file_path}")
                frame = pd.read_csv(file_path)
                frame['__season_key'] = _extract_season_from_path(file_path)
                frames.append(frame)
            except Exception as e:
                print(f"Failed to load {file_path}: {e}")
        if frames:
            df = pd.concat(frames, ignore_index=True)

    # If no usable data is found, back off to synthetic training data.
    if df is None or df.empty:
        df = create_dummy_model()

    X, y = build_training_dataset(df)
    
    print(f"Training with {len(X)} samples and {X.shape[1]} features")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Hyperparameter tuning for logistic regression.
    param_grid = {
        'C': [0.01, 0.1, 1.0, 3.0, 10.0],
        'class_weight': [None, 'balanced'],
        'solver': ['lbfgs']
    }

    grid = GridSearchCV(
        LogisticRegression(max_iter=5000, random_state=42),
        param_grid=param_grid,
        scoring='roc_auc',
        cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42),
        n_jobs=-1,
        refit=True,
    )
    grid.fit(X_train_scaled, y_train)
    best_params = grid.best_params_

    # Fit a calibrated logistic regression model to improve probability reliability.
    base_logit = LogisticRegression(
        C=best_params['C'],
        class_weight=best_params['class_weight'],
        solver=best_params['solver'],
        max_iter=5000,
        random_state=42,
    )

    model = CalibratedClassifierCV(
        estimator=base_logit,
        method='sigmoid',
        cv=5,
    )
    model.fit(X_train_scaled, y_train)

    # Fit an interpretable baseline model with the same params for coefficient reporting.
    coef_model = LogisticRegression(
        C=best_params['C'],
        class_weight=best_params['class_weight'],
        solver=best_params['solver'],
        max_iter=5000,
        random_state=42,
    )
    coef_model.fit(X_train_scaled, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test_scaled)
    y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
    
    random_split_metrics = _print_metrics("Random Split Performance", y_test, y_pred, y_pred_proba)
    print(f"Best Params: {best_params}")
    print(f"Home team win rate in test set: {y_test.mean():.3f}")
    print(f"Predicted home win rate: {y_pred.mean():.3f}")

    time_split_metrics = None
    if '__season_key' in df.columns:
        season_values = sorted([s for s in df['__season_key'].dropna().unique() if s])
        if len(season_values) >= 2:
            holdout_season = season_values[-1]
            train_df = df[df['__season_key'] != holdout_season].copy()
            holdout_df = df[df['__season_key'] == holdout_season].copy()

            if not train_df.empty and not holdout_df.empty:
                X_time_train, y_time_train = build_training_dataset(train_df)
                X_time_test, y_time_test = build_training_dataset(holdout_df)

                time_scaler = StandardScaler()
                X_time_train_scaled = time_scaler.fit_transform(X_time_train)
                X_time_test_scaled = time_scaler.transform(X_time_test)

                time_base = LogisticRegression(
                    C=best_params['C'],
                    class_weight=best_params['class_weight'],
                    solver=best_params['solver'],
                    max_iter=5000,
                    random_state=42,
                )
                time_model = CalibratedClassifierCV(
                    estimator=time_base,
                    method='sigmoid',
                    cv=5,
                )
                time_model.fit(X_time_train_scaled, y_time_train)

                time_pred = time_model.predict(X_time_test_scaled)
                time_prob = time_model.predict_proba(X_time_test_scaled)[:, 1]

                print(f"\n🕒 Time-Based Holdout Season: {holdout_season}")
                time_split_metrics = _print_metrics(
                    "Latest-Season Holdout Performance",
                    y_time_test,
                    time_pred,
                    time_prob,
                )
    
    # Save model and scaler
    model_path = os.path.join(base_dir, 'model.pkl')
    scaler_path = os.path.join(base_dir, 'scaler.pkl')
    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)

    # Save timestamped artifacts for reproducibility and rollback.
    version_tag = datetime.now().strftime('%Y_%m_%d_%H%M%S')
    versioned_model_name = f'model_{version_tag}.pkl'
    versioned_scaler_name = f'scaler_{version_tag}.pkl'
    versioned_model_path = os.path.join(base_dir, versioned_model_name)
    versioned_scaler_path = os.path.join(base_dir, versioned_scaler_name)
    joblib.dump(model, versioned_model_path)
    joblib.dump(scaler, versioned_scaler_path)

    metadata = {
        'created_at': datetime.now().isoformat(),
        'model_file': versioned_model_name,
        'scaler_file': versioned_scaler_name,
        'feature_count': int(X.shape[1]),
        'samples': int(len(X)),
        'best_params': best_params,
        'random_split_metrics': random_split_metrics,
        'time_split_metrics': time_split_metrics,
    }
    metadata_path = os.path.join(base_dir, 'model_metadata.json')
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n💾 Model saved:")
    print(f"- model.pkl ({os.path.getsize(model_path)/1024:.1f} KB)")
    print(f"- scaler.pkl ({os.path.getsize(scaler_path)/1024:.1f} KB)")
    print(f"- {versioned_model_name} ({os.path.getsize(versioned_model_path)/1024:.1f} KB)")
    print(f"- {versioned_scaler_name} ({os.path.getsize(versioned_scaler_path)/1024:.1f} KB)")
    print(f"- model_metadata.json")

    # Show coefficient magnitude to help interpret linear model behavior.
    coef_df = pd.DataFrame({
        'feature': X.columns,
        'coefficient': coef_model.coef_[0],
        'abs_coefficient': np.abs(coef_model.coef_[0])
    }).sort_values('abs_coefficient', ascending=False)

    print("\n🎯 Top 10 Logistic Regression Coefficients (by magnitude):")
    for _, row in coef_df.head(10).iterrows():
        print(f"  {row['feature']}: {row['coefficient']:.4f}")
    
    return model, scaler

if __name__ == "__main__":
    try:
        train_model()
        print("\n✅ Model training completed successfully!")
    except Exception as e:
        print(f"\n❌ Training failed: {str(e)}")
        import traceback
        traceback.print_exc()