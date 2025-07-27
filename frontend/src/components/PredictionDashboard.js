import React, { useState, useEffect } from "react";
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
  const [season, setSeason] = useState("2023-2024");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [teamStats, setTeamStats] = useState(null);
  const [backendReady, setBackendReady] = useState(false);
  const [retryCount, setRetryCount] = useState(0);

  // Enhanced backend health check with retries
  useEffect(() => {
    const checkBackend = async () => {
      try {
        const res = await axios.get(
          "https://the-bench-prophet.onrender.com/api/health",
          { timeout: 3000 }
        );
        
        if (res.data.status === "healthy") {
          setBackendReady(true);
          setError(null);
        } else {
          throw new Error("Backend not ready");
        }
      } catch (err) {
        if (retryCount < 10) { // Try for ~30 seconds total
          setTimeout(() => {
            setRetryCount(c => c + 1);
          }, 3000);
        } else {
          setError("Backend is taking longer than expected to start. Please refresh the page.");
        }
      }
    };

    checkBackend();
  }, [retryCount]);

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
          away_team: awayTeam,
          season: season
        },
        {
          headers: {
            "Content-Type": "application/json"
          },
          timeout: 10000 // 10 second timeout
        }
      );
      
      setResult(response.data);
      if (response.data.team_stats) {
        setTeamStats(response.data.team_stats);
      }
    } catch (err) {
      let errorMessage = "Prediction failed. Please try again.";
      if (err.response) {
        errorMessage = err.response.data?.error || 
                      `Server error: ${err.response.status}`;
      } else if (err.code === "ECONNABORTED") {
        errorMessage = "Request timed out. The backend might be overloaded.";
      } else {
        errorMessage = `Error: ${err.message}`;
      }
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
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
      {stats ? (
        <div className="stats-grid">
          <div className="stat">
            <span className="stat-label">Wins</span>
            <span className="stat-value">{stats.wins || 0}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Losses</span>
            <span className="stat-value">{stats.losses || 0}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Win %</span>
            <span className="stat-value">
              {stats.recent_win_pct ? (stats.recent_win_pct * 100).toFixed(1) : 'N/A'}%
            </span>
          </div>
          <div className="stat">
            <span className="stat-label">PPG</span>
            <span className="stat-value">{stats.ppg ? stats.ppg.toFixed(1) : 'N/A'}</span>
          </div>
        </div>
      ) : (
        <p>No stats available</p>
      )}
    </div>
  );

  return (
    <div className="dashboard-content">
      <div className="dashboard-header">
        <h1>🏀 The Bench Prophet</h1>
        <p>NBA Game Outcome Predictor</p>
        
        <div className="backend-status">
          {backendReady ? (
            <span className="status-connected">✅ Backend Connected</span>
          ) : (
            <span className="status-connecting">
              🔄 Connecting ({retryCount * 3}s elapsed)...
            </span>
          )}
        </div>
      </div>

      <form onSubmit={handlePredict} className="prediction-form">
        <div className="team-selection">
          <div className="team-selector">
            <label>🏠 Home Team</label>
            <select 
              value={homeTeam} 
              onChange={(e) => setHomeTeam(e.target.value)}
              className="team-select"
              disabled={loading}
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
              disabled={loading}
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

        <div className="season-selector">
          <label>🏆 Season</label>
          <select
            value={season}
            onChange={(e) => setSeason(e.target.value)}
            className="season-select"
            disabled={loading}
          >
            <option value="2023-2024">2023-2024</option>
            <option value="2022-2023">2022-2023</option>
            <option value="2021-2022">2021-2022</option>
          </select>
        </div>

        <button 
          type="submit" 
          disabled={!backendReady || loading || !homeTeam || !awayTeam}
          className={`predict-button ${!backendReady ? "button-pulse" : ""}`}
        >
          {loading ? (
            <>
              <span className="spinner"></span>
              Predicting...
            </>
          ) : (
            backendReady ? "🔮 Predict Game Outcome" : "⏳ Backend Starting"
          )}
        </button>

        {!backendReady && retryCount >= 10 && (
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="refresh-button"
          >
            🔄 Refresh Page
          </button>
        )}
      </form>

      {error && (
        <div className="error-message">
          <span>⚠️</span>
          <div>
            <strong>Error:</strong> {error}
            {error.includes("backend") && (
              <p className="retry-note">
                Render.com free instances sleep after inactivity. Try refreshing in 30 seconds.
              </p>
            )}
          </div>
        </div>
      )}

      {result && (
        <div className="results-section">
          <div className="prediction-result">
            <h2>🎯 Prediction Results</h2>
            <div className="winner-announcement">
              <h3>
                Predicted Winner: <span className="winner-name">
                  {result.predicted_winner || getTeamLabel(result.prediction === 1 ? homeTeam : awayTeam)}
                </span>
              </h3>
              <p className="confidence">
                Confidence: {Math.round(
                  Math.max(
                    result.home_win_prob || 0, 
                    result.away_win_prob || 0
                  ) * 100
                )}%
              </p>
            </div>
          </div>

          <div className="probability-section">
            <h3>📊 Win Probabilities</h3>
            <WinProbabilityBar 
              homeProb={(result.home_win_prob || 0) * 100}
              awayProb={(result.away_win_prob || 0) * 100}
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
        </div>
      )}

      {loading && (
        <div className="loading-overlay">
          <div className="spinner"></div>
          <p>Crunching the numbers...</p>
        </div>
      )}
    </div>
  );
};

export default PredictionDashboard;