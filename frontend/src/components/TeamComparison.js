import React, { useState } from "react";
import axios from "axios";
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from "recharts";

const TeamComparison = () => {
  const [team1, setTeam1] = useState("");
  const [team2, setTeam2] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const teams = [
    "ATL", "BOS", "BKN", "CHA", "CHI", "CLE", "DAL", "DEN",
    "DET", "GSW", "HOU", "IND", "LAC", "LAL", "MEM", "MIA",
    "MIL", "MIN", "NOP", "NYK", "OKC", "ORL", "PHI", "PHX",
    "POR", "SAC", "SAS", "TOR", "UTA", "WAS"
  ];
  
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
    const teamA = result[team1];
    const teamB = result[team2];
    return Object.keys(teamA).map((stat) => ({
      stat,
      [team1]: teamA[stat],
      [team2]: teamB[stat]
    }));
  };

  return (
    <div className="dashboard-content">
      <h2>Compare Two NBA Teams</h2>
      <form onSubmit={handleCompare}>
        <label>Team 1:</label>
        <select value={team1} onChange={(e) => setTeam1(e.target.value)} required>
          <option value="">-- Select Team 1 --</option>
          {teams.map((team) => (
            <option key={team} value={team}>{team}</option>
          ))}
        </select>

        <label>Team 2:</label>
        <select value={team2} onChange={(e) => setTeam2(e.target.value)} required>
          <option value="">-- Select Team 2 --</option>
          {teams.map((team) => (
            <option key={team} value={team}>{team}</option>
          ))}
        </select>

        <button type="submit" disabled={loading}>
          {loading ? "Comparing..." : "Compare Teams"}
        </button>
      </form>

      {result && (
        <div style={{ marginTop: "2rem" }}>
          <h3>📊 Comparison Result</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={prepareChartData()} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
              <XAxis dataKey="stat" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey={team1} fill="#007bff" />
              <Bar dataKey={team2} fill="#28a745" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {error && <p style={{ color: "red", marginTop: "1rem" }}>{error}</p>}
    </div>
  );
};

export default TeamComparison;
