import React, { useState } from "react";
import axios from "axios";
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from "recharts";

const TEAM_MAP = {
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
};

const TeamComparison = () => {
  const [team1, setTeam1] = useState("");
  const [team2, setTeam2] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const teams = Object.keys(TEAM_MAP);

  const handleCompare = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await axios.get(
        `https://the-bench-prophet.onrender.com/api/compare-teams?team1=${team1}&team2=${team2}`
      );
      setResult(response.data);
    } catch (err) {
      setError("Team comparison failed. Check spelling or try again.");
    }

    setLoading(false);
  };

  const prepareChartData = () => {
    if (!result) return [];

    const teamAKey = team1;
    const teamBKey = team2;

    const teamA = result[teamAKey];
    const teamB = result[teamBKey];

    if (!teamA || !teamB) return [];

    return Object.keys(teamA).map((stat) => ({
      stat,
      [teamAKey]: teamA[stat],
      [teamBKey]: teamB[stat]
    }));
  };

  const chartData = prepareChartData();

  return (
    <div className="dashboard-content">
      <h2>Compare Two NBA Teams</h2>
      <form onSubmit={handleCompare}>
        <label>Team 1:</label>
        <select value={team1} onChange={(e) => setTeam1(e.target.value)} required>
          <option value="">-- Select Team 1 --</option>
          {teams.map((team) => (
            <option key={team} value={team}>{TEAM_MAP[team]}</option>
          ))}
        </select>

        <label>Team 2:</label>
        <select value={team2} onChange={(e) => setTeam2(e.target.value)} required>
          <option value="">-- Select Team 2 --</option>
          {teams.map((team) => (
            <option key={team} value={team}>{TEAM_MAP[team]}</option>
          ))}
        </select>

        <button type="submit" disabled={loading}>
          {loading ? "Comparing..." : "Compare Teams"}
        </button>
      </form>

      {chartData.length > 0 && (
        <div style={{ marginTop: "2rem" }}>
          <h3>📊 Comparison Result</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
              <XAxis dataKey="stat" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey={Object.keys(chartData[0])[1]} fill="#007bff" />
              <Bar dataKey={Object.keys(chartData[0])[2]} fill="#28a745" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {error && <p style={{ color: "red", marginTop: "1rem" }}>{error}</p>}

      {result && chartData.length === 0 && (
        <p style={{ color: 'red', marginTop: '1rem' }}>
          ⚠️ Could not find stats for one or both teams. Try different selections.
        </p>
      )}
    </div>
  );
};

export default TeamComparison;
