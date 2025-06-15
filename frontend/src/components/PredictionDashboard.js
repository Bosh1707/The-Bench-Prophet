import React, { useState } from "react";
import axios from "axios";

const PredictionDashboard = () => {
  const [formData, setFormData] = useState({
    "Recent Win % (Home)": "",
    "Recent Losses (Home)": "",
    "Recent Win % (Visitor)": "",
    "Recent Losses (Visitor)": "",
    "Matchup Wins (Home)": "",
    "Matchup Wins (Visitor)": "",
    "DSLG (Home)": "",
    "DSLG (Visitor)": "",
    "Wins (Home)": "",
    "Losses (Home)": "",
    "Wins (Visitor)": "",
    "Losses (Visitor)": ""
  });

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post(
        "https://the-bench-prophet.onrender.com/api/predict",
        Object.fromEntries(
          Object.entries(formData).map(([k, v]) => [k, parseFloat(v)])
        )
      );
      setResult(response.data);
    } catch (err) {
      setError("Prediction failed. Please try again.");
    }
    setLoading(false);
  };

  return (
    <div className="dashboard-content">
      <h2>Game Outcome Predictor</h2>
      <form onSubmit={handleSubmit}>
        {Object.keys(formData).map((key) => (
          <div key={key}>
            <input
              type="number"
              name={key}
              value={formData[key]}
              onChange={handleChange}
              placeholder={key}
              required
            />
          </div>
        ))}
        <button type="submit" disabled={loading}>
          {loading ? "Predicting..." : "Get Prediction"}
        </button>
      </form>

      {result && (
        <div style={{ marginTop: "2rem" }}>
          <h3>📈 Prediction Result</h3>
          <p><strong>{result.prediction}</strong></p>
          <p>Home Win Probability: {Math.round(result.probabilities.home_win * 100)}%</p>
          <p>Visitor Win Probability: {Math.round(result.probabilities.visitor_win * 100)}%</p>
        </div>
      )}

      {error && <p style={{ color: "red", marginTop: "1rem" }}>{error}</p>}
    </div>
  );
};

export default PredictionDashboard;
