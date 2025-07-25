import React, { useState } from "react";
import axios from "axios";
import "./PredictionDashboard.css";

const TEAM_OPTIONS = [
  { value: "ATL", label: "Atlanta Hawks" },
  { value: "BOS", label: "Boston Celtics" },
  { value: "BKN", label: "Brooklyn Nets" },
  { value: "CHA", label: "Charlotte Hornets" },
  { value: "CHI", label: "Chicago Bulls" },
  { value: "CLE", label: "Cleveland Cavaliers" },
  { value: "DAL", label: "Dallas Mavericks" },
  { value: "DEN", label: "Denver Nuggets" },
  { value: "DET", label: "Detroit Pistons" },
  { value: "GSW", label: "Golden State Warriors" },
  { value: "HOU", label: "Houston Rockets" },
  { value: "IND", label: "Indiana Pacers" },
  { value: "LAC", label: "Los Angeles Clippers" },
  { value: "LAL", label: "Los Angeles Lakers" },
  { value: "MEM", label: "Memphis Grizzlies" },
  { value: "MIA", label: "Miami Heat" },
  { value: "MIL", label: "Milwaukee Bucks" },
  { value: "MIN", label: "Minnesota Timberwolves" },
  { value: "NOP", label: "New Orleans Pelicans" },
  { value: "NYK", label: "New York Knicks" },
  { value: "OKC", label: "Oklahoma City Thunder" },
  { value: "ORL", label: "Orlando Magic" },
  { value: "PHI", label: "Philadelphia 76ers" },
  { value: "PHX", label: "Phoenix Suns" },
  { value: "POR", label: "Portland Trail Blazers" },
  { value: "SAC", label: "Sacramento Kings" },
  { value: "SAS", label: "San Antonio Spurs" },
  { value: "TOR", label: "Toronto Raptors" },
  { value: "UTA", label: "Utah Jazz" },
  { value: "WAS", label: "Washington Wizards" }
];

const PredictionDashboard = () => {
  const [homeTeam, setHomeTeam] = useState("");
  const [awayTeam, setAwayTeam] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [teamStats, setTeamStats] = useState(null);

  const handlePredict = async (e) => {
    e.preventDefault();
    
    if (!homeTeam || !awayTeam) {
      setError("Please select both teams");
      return;
    }
    
    if (homeTeam === awayTeam) {
      setError("Please select different teams");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    setTeamStats(null);

    try {
      const response = await axios.post(
        "https://the-bench-prophet.onrender.com/api/predict-teams",
        {
          home_team: homeTeam,
          away_team: awayTeam
        }
      );
      
      setResult(response.data);
      if (response.data.team_stats) {
        setTeamStats(response.data.team_stats);
      }
    } catch (err) {
      console.error("Prediction error:", err);
      setError(
        err.response?.data?.error || 
        "Prediction failed. Please try again."
      );
    }
    
    setLoading(false);
  };

  const getTeamLabel = (abbreviation) => {
    const team = TEAM_OPTIONS.find(t => t.value === abbreviation);
    return team ? team.label : abbreviation;
  };

  const WinProbabilityBar = ({ homeProb, awayProb, homeTeam, awayTeam }) => (
    <div className="probability-container">
      <div className="probability-labels">
        <span className="home-label">{getTeamLabel(homeTeam)}</span>
        <span className="away-label">{getTeamLabel(awayTeam)}</span>
      </div>
      <div className="probability-bar">
        <div 
          className="home-prob" 
          style={{ width: `${homeProb}%` }}
        >
          {Math.round(homeProb)}%
        </div>
        <div 
          className="away-prob" 
          style={{ width: `${awayProb}%` }}
        >
          {Math.round(awayProb)}%
        </div>
      </div>
    </div>
  );

  const TeamStatsCard = ({ team, stats, isHome }) => (
    <div className={`team-stats-card ${isHome ? 'home' : 'away'}`}>
      <h4>{isHome ? '🏠' : '✈️'} {getTeamLabel(team)}</h4>
      <div className="stats-grid">
        <div className="stat">
          <span className="stat-label">Wins</span>
          <span className="stat-value">{stats.wins}</span>
        </div>
        <div className="stat">
          <span className="stat-label">Losses</span>
          <span className="stat-value">{stats.losses}</span>
        </div>
        <div className="stat">
          <span className="stat-label">Recent Win %</span>
          <span className="stat-value">{(stats.recent_win_pct * 100).toFixed(1)}%</span>
        </div>
        <div className="stat">
          <span className="stat-label">Recent Losses</span>
          <span className="stat-value">{stats.recent_losses}</span>
        </div>
      </div>
    </div>
  );

  return (
    <div className="dashboard-content">
      <div className="dashboard-header">
        <h1>🏀 The Bench Prophet</h1>
        <p>NBA Game Outcome Predictor</p>
      </div>

      <form onSubmit={handlePredict} className="prediction-form">
        <div className="team-selection">
          <div className="team-selector">
            <label>🏠 Home Team</label>
            <select 
              value={homeTeam} 
              onChange={(e) => setHomeTeam(e.target.value)}
              className="team-select"
            >
              <option value="">Select Home Team</option>
              {TEAM_OPTIONS.map((team) => (
                <option key={team.value} value={team.value}>
                  {team.value} - {team.label}
                </option>
              ))}
            </select>
          </div>

          <div className="vs-divider">VS</div>

          <div className="team-selector">
            <label>✈️ Away Team</label>
            <select 
              value={awayTeam} 
              onChange={(e) => setAwayTeam(e.target.value)}
              className="team-select"
            >
              <option value="">Select Away Team</option>
              {TEAM_OPTIONS.map((team) => (
                <option key={team.value} value={team.value}>
                  {team.value} - {team.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <button 
          type="submit" 
          disabled={loading || !homeTeam || !awayTeam}
          className="predict-button"
        >
          {loading ? (
            <span>
              <span className="spinner"></span>
              Analyzing Teams...
            </span>
          ) : (
            "🔮 Predict Game Outcome"
          )}
        </button>
      </form>

      {error && (
        <div className="error-message">
          <span>❌</span>
          {error}
        </div>
      )}

      {result && (
        <div className="results-section">
          <div className="prediction-result">
            <h2>🎯 Prediction Results</h2>
            <div className="winner-announcement">
              <h3>
                Predicted Winner: <strong>{result.predicted_winner}</strong>
              </h3>
              <p className="confidence">
                Confidence: {Math.round(Math.max(result.home_win_prob, result.away_win_prob) * 100)}%
              </p>
            </div>
          </div>

          <div className="probability-section">
            <h3>📊 Win Probabilities</h3>
            <WinProbabilityBar 
              homeProb={result.home_win_prob * 100}
              awayProb={result.away_win_prob * 100}
              homeTeam={homeTeam}
              awayTeam={awayTeam}
            />
          </div>

          {teamStats && (
            <div className="team-stats-section">
              <h3>📈 Team Statistics</h3>
              <div className="stats-comparison">
                <TeamStatsCard 
                  team={homeTeam} 
                  stats={teamStats.home} 
                  isHome={true}
                />
                <TeamStatsCard 
                  team={awayTeam} 
                  stats={teamStats.away} 
                  isHome={false}
                />
              </div>
            </div>
          )}

          {result.matchup_record && (
            <div className="matchup-section">
              <h3>🥊 Head-to-Head Record</h3>
              <div className="matchup-stats">
                <div className="matchup-stat">
                  <span>{getTeamLabel(homeTeam)}</span>
                  <span className="record">{result.matchup_record.home_wins}</span>
                </div>
                <div className="matchup-divider">-</div>
                <div className="matchup-stat">
                  <span>{getTeamLabel(awayTeam)}</span>
                  <span className="record">{result.matchup_record.away_wins}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PredictionDashboard;
