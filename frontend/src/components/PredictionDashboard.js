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

const API_BASE_URL = "https://the-bench-prophet.onrender.com";

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
  const [wakingUp, setWakingUp] = useState(false);

  // Enhanced axios configuration with better error handling
  const apiClient = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000, // 30 second timeout for initial requests
    headers: {
      'Content-Type': 'application/json'
    }
  });

  // Add response interceptor for better error handling
  apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
      console.error('API Error:', error);
      
      if (error.code === 'ECONNABORTED') {
        return Promise.reject(new Error('Request timed out. Backend may be sleeping.'));
      }
      
      if (error.message === 'Network Error' || error.code === 'ERR_NETWORK') {
        return Promise.reject(new Error('Network connection failed. Backend may be sleeping.'));
      }
      
      return Promise.reject(error);
    }
  );

  // Backend health check with exponential backoff
  useEffect(() => {
    let isMounted = true;
    const maxRetries = 15; // Increase max retries
    
    const getBackoffDelay = (attempt) => {
      return Math.min(1000 * Math.pow(1.5, attempt), 10000); // Max 10 seconds
    };

    const checkBackend = async () => {
      if (!isMounted) return;
      
      try {
        console.log(`Health check attempt ${retryCount + 1}/${maxRetries}`);
        
        const res = await apiClient.get('/api/health');
        
        if (isMounted) {
          if (res.data.status === "healthy") {
            setBackendReady(true);
            setError(null);
            setWakingUp(false);
            console.log('✅ Backend is healthy');
          } else {
            throw new Error(`Backend status: ${res.data.status}`);
          }
        }
      } catch (err) {
        console.error('Health check failed:', err.message);
        
        if (isMounted && retryCount < maxRetries) {
          setWakingUp(true);
          const delay = getBackoffDelay(retryCount);
          console.log(`Retrying in ${delay}ms...`);
          
          setTimeout(() => {
            if (isMounted) setRetryCount(c => c + 1);
          }, delay);
        } else if (isMounted) {
          setError("Backend is taking longer than expected to start. Please try refreshing the page.");
          setBackendReady(false);
          setWakingUp(false);
        }
      }
    };

    checkBackend();

    return () => {
      isMounted = false;
    };
  }, [retryCount]);

  // Keep-alive ping when backend is ready
  useEffect(() => {
    if (backendReady) {
      const interval = setInterval(async () => {
        try {
          await apiClient.get('/api/health');
        } catch (err) {
          console.warn('Keep-alive ping failed:', err.message);
          // Don't immediately mark as unhealthy, but prepare for potential issues
        }
      }, 240000); // Ping every 4 minutes

      return () => clearInterval(interval);
    }
  }, [backendReady]);

  const handlePredict = async (e) => {
    e.preventDefault();
    
    if (!backendReady) {
      setError("Backend is still starting up. Please wait...");
      return;
    }

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

    // Retry logic for predictions
    const maxPredictionRetries = 3;
    let attempt = 0;

    while (attempt < maxPredictionRetries) {
      try {
        console.log(`Prediction attempt ${attempt + 1}/${maxPredictionRetries}`);
        
        const response = await apiClient.post('/api/predict-teams', {
          home_team: homeTeam,
          away_team: awayTeam,
          season: season
        });
        
        // Success - break out of retry loop
        setResult(response.data);
        if (response.data.stats && response.data.stats.teams) {
          setTeamStats(response.data.stats.teams);
        }
        console.log('✅ Prediction successful');
        console.log('Response data:', response.data); // Debug log
        break;
        
      } catch (err) {
        attempt++;
        console.error(`Prediction attempt ${attempt} failed:`, err.message);
        
        if (attempt >= maxPredictionRetries) {
          // All retries exhausted
          let errorMessage = "Prediction failed after multiple attempts.";
          
          if (err.message.includes('timed out') || err.message.includes('sleeping')) {
            errorMessage = "Backend appears to be sleeping. Please wait 30-60 seconds and try again.";
            setBackendReady(false); // Trigger health check restart
            setRetryCount(0);
          } else if (err.response) {
            errorMessage = err.response.data?.error || `Server error: ${err.response.status}`;
          } else if (err.message.includes('Network')) {
            errorMessage = "Network connection failed. Please check your internet connection.";
          }
          
          setError(errorMessage);
        } else {
          // Wait before retry
          await new Promise(resolve => setTimeout(resolve, 2000 * attempt));
        }
      }
    }

    setLoading(false);
  };

  const handleRefresh = () => {
    setRetryCount(0);
    setBackendReady(false);
    setWakingUp(false);
    setError(null);
    window.location.reload();
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
      <h4>{isHome ? '🏠' : '✈️'} {stats?.name || getTeamLabel(team)}</h4>
      {stats ? (
        <div className="stats-grid">
          <div className="stat">
            <span className="stat-label">Record</span>
            <span className="stat-value">{stats.wins || 0}-{stats.losses || 0}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Games</span>
            <span className="stat-value">{stats.games_played || 0}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Win %</span>
            <span className="stat-value">
              {stats.win_pct ? (stats.win_pct * 100).toFixed(1) : '0.0'}%
            </span>
          </div>
          <div className="stat">
            <span className="stat-label">PPG</span>
            <span className="stat-value">{stats.ppg ? stats.ppg.toFixed(1) : '0.0'}</span>
          </div>
        </div>
      ) : (
        <p>No stats available</p>
      )}
    </div>
  );

  const getStatusMessage = () => {
    if (backendReady) {
      return { text: "✅ Backend Connected", class: "success" };
    } else if (wakingUp) {
      const elapsed = retryCount * 2; // Approximate seconds
      return { 
        text: `⏳ Waking up backend... (${elapsed}s elapsed)`, 
        class: "warning" 
      };
    } else if (error && error.includes('longer than expected')) {
      return { text: "❌ Connection Failed", class: "error" };
    } else {
      return { text: "🔄 Connecting...", class: "warning" };
    }
  };

  const status = getStatusMessage();

  return (
    <div className="dashboard-content">
      <div className="dashboard-header">
        <h1>🏀 The Bench Prophet</h1>
        <p>NBA Game Outcome Predictor</p>
        
        <div className="backend-status">
          <div className={`status-badge ${status.class}`}>
            {status.text}
            {(!backendReady || error) && (
              <button onClick={handleRefresh} className="refresh-btn">
                Refresh
              </button>
            )}
          </div>
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
          className={`predict-button ${wakingUp ? "button-pulse" : ""}`}
        >
          {loading ? (
            <>
              <span className="spinner"></span>
              Predicting...
            </>
          ) : (
            backendReady ? "🔮 Predict Game Outcome" : "⏳ Awaiting Backend"
          )}
        </button>
      </form>

      {error && (
        <div className="error-message">
          <span>⚠️</span>
          <div>
            <strong>Error:</strong> {error}
            {error.includes("sleeping") && (
              <p className="retry-note">
                Free hosting services sleep after inactivity. The backend should wake up in 30-60 seconds.
              </p>
            )}
            {error.includes("Connection Failed") && (
              <p className="retry-note">
                Try refreshing the page or check your internet connection.
              </p>
            )}
          </div>
        </div>
      )}

      {result && (
        <div className="results-section">
          {/* Debug section - remove this in production */}
          {process.env.NODE_ENV === 'development' && (
            <details style={{ marginBottom: '20px', padding: '10px', background: '#f5f5f5', borderRadius: '5px' }}>
              <summary style={{ cursor: 'pointer', fontWeight: 'bold' }}>🐛 Debug: Raw Response Data</summary>
              <pre style={{ fontSize: '12px', overflow: 'auto', maxHeight: '200px' }}>
                {JSON.stringify(result, null, 2)}
              </pre>
            </details>
          )}

          <div className="prediction-result">
            <h2>🎯 Prediction Results</h2>
            <div className="winner-announcement">
              <h3>
                Predicted Winner: <span className="winner-name">
                  {result.prediction?.winner || "Unknown"}
                </span>
              </h3>
              <p className="confidence">
                Confidence: {result.prediction?.confidence || 0}%
              </p>
            </div>
          </div>

          <div className="probability-section">
            <h3>📊 Win Probabilities</h3>
            <WinProbabilityBar 
              homeProb={result.prediction?.probabilities?.home || 0}
              awayProb={result.prediction?.probabilities?.away || 0}
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

          {result.stats?.matchup && (result.stats.matchup.home_wins > 0 || result.stats.matchup.away_wins > 0) && (
            <div className="matchup-section">
              <h3>🥊 Head-to-Head Record ({result.stats.matchup.history?.total_games || 0} games)</h3>
              <div className="matchup-stats">
                <div className="matchup-stat">
                  <span>{getTeamLabel(homeTeam)}</span>
                  <span className="record">{result.stats.matchup.home_wins || 0}</span>
                </div>
                <div className="matchup-divider">-</div>
                <div className="matchup-stat">
                  <span>{getTeamLabel(awayTeam)}</span>
                  <span className="record">{result.stats.matchup.away_wins || 0}</span>
                </div>
              </div>
              {result.stats.matchup.history && (
                <p style={{ textAlign: 'center', marginTop: '10px', color: '#666' }}>
                  Home team wins {result.stats.matchup.history.home_win_pct.toFixed(1)}% of matchups
                </p>
              )}
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