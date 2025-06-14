import pandas as pd
from sklearn.linear_model import LogisticRegression
import joblib   

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

def train_model(csv_path):
    data = pd.read_csv(csv_path)
    data['Home_Team_Won'] = (data['Home_PTS'] > data['Visitor_PTS']).astype(int)

    X = data[['Recent Win % (Home)', 'Recent Losses (Home)',
              'Recent Win % (Visitor)', 'Recent Losses (Visitor)',
              'Matchup Wins (Home)', 'Matchup Wins (Visitor)',
              'DSLG (Home)', 'DSLG (Visitor)',
              'Wins (Home)', 'Losses (Home)', 'Wins (Visitor)', 'Losses (Visitor)']]
    y = data['Home_Team_Won']
    X = X.fillna(0)

    model = LogisticRegression(random_state=42, max_iter=2000)
    model.fit(X, y)
    joblib.dump(model, 'model.pkl')
    return model

def predict(model, features: dict):
    X = pd.DataFrame([features])
    return model.predict(X)[0], model.predict_proba(X)[0].tolist()

def get_team_stats(data: pd.DataFrame, team: str):
    # Convert abbreviation to full name if needed
    team = TEAM_ABBREVIATIONS.get(team.upper(), team)

    team_home = data[data['Home/Neutral'] == team].sort_values('Date', ascending=False)
    team_away = data[data['Visitor/Neutral'] == team].sort_values('Date', ascending=False)
    recent = pd.concat([team_home, team_away]).sort_values('Date', ascending=False)

    if recent.empty:
        return None

    latest = recent.iloc[0]
    return {
        "Wins": int(latest[f"Wins (Home)"] if latest["Home/Neutral"] == team else latest["Wins (Visitor)"]),
        "Losses": int(latest[f"Losses (Home)"] if latest["Home/Neutral"] == team else latest["Losses (Visitor)"]),
        "Recent Win %": float(latest[f"Recent Win % (Home)"] if latest["Home/Neutral"] == team else latest["Recent Win % (Visitor)"]),
        "Recent Losses": int(latest[f"Recent Losses (Home)"] if latest["Home/Neutral"] == team else latest["Recent Losses (Visitor)"])
    }
