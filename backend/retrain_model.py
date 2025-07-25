import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib
import sklearn
print("scikit-learn version:", sklearn.__version__)  # Verify it's 1.0.2

# Load your data (adjust paths as needed)
data = pd.read_csv("data/nba_2021_2022_final_data.csv")  

# Minimal feature engineering (customize for your actual data)
features = data[["Wins (Home)", "Losses (Home)", "Wins (Visitor)", "Losses (Visitor)"]]
target = (data["Home_PTS"] > data["Visitor_PTS"]).astype(int)

# Train model
model = RandomForestClassifier(
    n_estimators=100,
    random_state=42,
    max_depth=5
)
model.fit(features, target)

# Save with protocol=4 for broader compatibility
joblib.dump(model, "model.pkl", protocol=4)
print("Model re-trained and saved with scikit-learn 1.0.2")