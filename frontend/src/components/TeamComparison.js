import React, { useState } from "react";
import axios from "axios";
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { Select, Button, Spin, Alert, Divider } from "antd";
import "./TeamComparison.css";
import 'antd/dist/reset.css'
const { Option } = Select;

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
  const [team1, setTeam1] = useState(null);
  const [team2, setTeam2] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [seasons, setSeasons] = useState(["2021-2022", "2022-2023", "2023-2024", "2024-2025"]);
  const [selectedSeason, setSelectedSeason] = useState("2024-2025");

  const teams = Object.keys(TEAM_MAP);

  const handleCompare = async (e) => {
    if (!team1 || !team2) {
      setError("Please select both teams");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await axios.get(
        `https://the-bench-prophet.onrender.com/api/compare`,
        {
          params: {
            team1,
            team2,
            season: selectedSeason
          }
        }
      );
      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.message || "Team comparison failed");
    } finally {
      setLoading(false);
    }
  };

  const prepareChartData = () => {
    if (!result) return [];

    return [
      {
        name: "Wins",
        [team1]: result[team1]?.wins || 0,
        [team2]: result[team2]?.wins || 0,
      },
      {
        name: "Points Per Game",
        [team1]: result[team1]?.ppg || 0,
        [team2]: result[team2]?.ppg || 0,
      },
      {
        name: "Head-to-Head Wins",
        [team1]: result.headToHead?.[team1] || 0,
        [team2]: result.headToHead?.[team2] || 0,
      },
    ];
  };

  const chartData = prepareChartData();
  const colors = ["#1f77b4", "#ff7f0e"]; // Customizable colors

  return (
    <div className="team-comparison-container">
      <h2>🏀 Team Comparison Tool</h2>
      
      <div className="comparison-controls">
        <div className="select-group">
          <label>Season:</label>
          <Select
            value={selectedSeason}
            onChange={setSelectedSeason}
            style={{ width: 200 }}
          >
            {seasons.map(season => (
              <Option key={season} value={season}>{season}</Option>
            ))}
          </Select>
        </div>

        <div className="select-group">
          <label>Team 1:</label>
          <Select
            showSearch
            value={team1}
            onChange={setTeam1}
            placeholder="Select first team"
            optionFilterProp="children"
            style={{ width: 200 }}
            filterOption={(input, option) =>
              option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
            }
          >
            {Object.entries(TEAM_MAP).map(([abbr, name]) => (
              <Option key={abbr} value={abbr}>{name}</Option>
            ))}
          </Select>
        </div>

        <div className="select-group">
          <label>Team 2:</label>
          <Select
            showSearch
            value={team2}
            onChange={setTeam2}
            placeholder="Select second team"
            optionFilterProp="children"
            style={{ width: 200 }}
            filterOption={(input, option) =>
              option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
            }
          >
            {Object.entries(TEAM_MAP).map(([abbr, name]) => (
              <Option key={abbr} value={abbr}>{name}</Option>
            ))}
          </Select>
        </div>

        <Button 
          type="primary" 
          onClick={handleCompare}
          loading={loading}
          disabled={!team1 || !team2}
        >
          Compare Teams
        </Button>
      </div>

      {error && (
        <Alert message={error} type="error" showIcon style={{ marginTop: 20 }} />
      )}

      {result && (
        <div className="results-section">
          <Divider orientation="left">Comparison Results</Divider>
          
          <div className="stats-grid">
            <div className="stat-card">
              <h3>{TEAM_MAP[team1]}</h3>
              <p>Wins: {result[team1]?.wins || 0}</p>
              <p>PPG: {result[team1]?.ppg?.toFixed(1) || 0}</p>
            </div>
            
            <div className="stat-card">
              <h3>Head-to-Head</h3>
              <p>{result.headToHead?.[team1] || 0} - {result.headToHead?.[team2] || 0}</p>
            </div>
            
            <div className="stat-card">
              <h3>{TEAM_MAP[team2]}</h3>
              <p>Wins: {result[team2]?.wins || 0}</p>
              <p>PPG: {result[team2]?.ppg?.toFixed(1) || 0}</p>
            </div>
          </div>

          <ResponsiveContainer width="100%" height={400}>
            <BarChart
              data={chartData}
              margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
              layout="vertical"
            >
              <XAxis type="number" />
              <YAxis dataKey="name" type="category" />
              <Tooltip />
              <Legend />
              <Bar dataKey={team1} name={TEAM_MAP[team1]} fill={colors[0]} />
              <Bar dataKey={team2} name={TEAM_MAP[team2]} fill={colors[1]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};

export default TeamComparison;