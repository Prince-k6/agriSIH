"""
train_model.py
--------------
Trains a machine learning model to predict the irrigation pump state (ON/OFF)
based on sensor readings.

Workflow:
1. Dataset Generation: Generates a synthetic dataset of 1,200 records by simulating
   different environmental scenarios (normal, dry_soil, hot_day, low_water, night)
   and logging the outcomes of the baseline rules.
2. Data Preprocessing: Loads the dataset, encodes target variables, and splits into train/test sets.
3. Model Training: Trains a Decision Tree Classifier and a Logistic Regression Classifier.
4. Evaluation: Calculates metrics (Accuracy, Precision, Recall, F1) for both models.
5. Serialization: Saves the best model (Decision Tree) and creates a JSON metadata file
   containing the performance metrics, feature importances, and text-based tree rules
   for the Streamlit dashboard to display.
"""

import os
import sys
import json
import pickle
import time
import random
import pandas as pd
import numpy as np

# Ensure sklearn is installed
try:
    from sklearn.model_selection import train_test_split
    from sklearn.tree import DecisionTreeClassifier, export_text
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, precision_recall_fscore_support
except ImportError:
    print("Error: scikit-learn is not installed. Please run: pip install -r requirements.txt")
    sys.exit(1)

# Include current directory in sys.path to load local simulator modules
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(CURRENT_DIR)

from sensor_simulator import SensorSimulator
from threshold_logic import evaluate

# Paths
DATA_DIR = os.path.join(CURRENT_DIR, "..", "data")
OUTPUTS_DIR = os.path.join(CURRENT_DIR, "..", "outputs")
TRAINING_DATA_PATH = os.path.join(DATA_DIR, "training_data.csv")
MODEL_PATH = os.path.join(OUTPUTS_DIR, "irrigation_model.pkl")
METADATA_PATH = os.path.join(OUTPUTS_DIR, "model_metadata.json")


def generate_dataset(num_records=1200):
    """Generate a balanced synthetic dataset of sensor readings and pump state decisions."""
    print(f"Generating {num_records} synthetic sensor readings...")
    os.makedirs(DATA_DIR, exist_ok=True)

    # Scenarios to simulate with their corresponding weights
    scenarios = ["normal", "dry_soil", "hot_day", "low_water", "night"]
    weights = [0.40, 0.20, 0.15, 0.15, 0.10]  # Balanced mix of conditions

    sim = SensorSimulator(scenario="normal")
    pump_state = False
    data_records = []

    for idx in range(num_records):
        # Periodically switch scenarios to generate diverse data and reset simulator state
        if idx % 15 == 0:
            scenario = random.choices(scenarios, weights=weights)[0]
            sim = SensorSimulator(scenario=scenario)

        reading = sim.read_all()
        result = evaluate(reading, pump_state)
        pump_state = result["pump_state"]
        alerts = result["alerts"]

        data_records.append({
            "soil_moisture": reading["soil_moisture"],
            "temperature": reading["temperature"],
            "humidity": reading["humidity"],
            "light": reading["light"],
            "water_level": reading["water_level"],
            "pump_state": "ON" if pump_state else "OFF"
        })

    # Save to CSV
    df = pd.DataFrame(data_records)
    df.to_csv(TRAINING_DATA_PATH, index=False)
    print(f"Dataset successfully created and saved to {TRAINING_DATA_PATH}")
    return df


def train_and_evaluate():
    """Load training data, train models, evaluate them, and serialize the best one."""
    os.makedirs(OUTPUTS_DIR, exist_ok=True)

    # 1. Load or Generate Dataset
    # We always regenerate the dataset to ensure it represents fresh simulation rules
    # and has balanced classes.
    df = generate_dataset()

    # 2. Preprocessing
    # Map target variable 'pump_state' to binary: ON = 1, OFF = 0
    df["target"] = df["pump_state"].map({"ON": 1, "OFF": 0})

    features = ["soil_moisture", "temperature", "humidity", "light", "water_level"]
    X = df[features]
    y = df["target"]

    # 3. Train/Test Split (80% Train, 20% Test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"Training set shape: {X_train.shape}, Test set shape: {X_test.shape}")

    # 4. Model 1: Decision Tree Classifier
    # We restrict max_depth to keep the rules simple and explainable
    dt = DecisionTreeClassifier(max_depth=4, random_state=42)
    dt.fit(X_train, y_train)
    y_pred_dt = dt.predict(X_test)

    # Evaluate Decision Tree
    acc_dt = accuracy_score(y_test, y_pred_dt)
    prec_dt, rec_dt, f1_dt, _ = precision_recall_fscore_support(
        y_test, y_pred_dt, average="binary"
    )

    print("\n--- Decision Tree Classifier Evaluation ---")
    print(f"Accuracy  : {acc_dt:.4f}")
    print(f"Precision : {prec_dt:.4f}")
    print(f"Recall    : {rec_dt:.4f}")
    print(f"F1-Score  : {f1_dt:.4f}")

    # Model Rules text export
    tree_rules = export_text(dt, feature_names=features)
    print("\nLearned Decision Tree Rules:")
    print(tree_rules)

    # 5. Model 2: Logistic Regression (For Comparison)
    lr = LogisticRegression(max_iter=1000, random_state=42)
    lr.fit(X_train, y_train)
    y_pred_lr = lr.predict(X_test)

    # Evaluate Logistic Regression
    acc_lr = accuracy_score(y_test, y_pred_lr)
    prec_lr, rec_lr, f1_lr, _ = precision_recall_fscore_support(
        y_test, y_pred_lr, average="binary"
    )

    print("\n--- Logistic Regression Evaluation ---")
    print(f"Accuracy  : {acc_lr:.4f}")
    print(f"Precision : {prec_lr:.4f}")
    print(f"Recall    : {rec_lr:.4f}")
    print(f"F1-Score  : {f1_lr:.4f}")

    # 6. Choose and Save the Best Model
    # Decision Tree is preferred here for explanation requirements
    best_model = dt
    print(f"\nSaving the Decision Tree model to {MODEL_PATH}...")
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(best_model, f)

    # 7. Create Metadata JSON for Dashboard Use
    importances = dict(zip(features, dt.feature_importances_))
    # Round values for display clarity
    importances = {k: round(v, 4) for k, v in importances.items()}

    metadata = {
        "model_type": "DecisionTreeClassifier",
        "trained_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "features": features,
        "metrics": {
            "decision_tree": {
                "accuracy": round(acc_dt, 4),
                "precision": round(prec_dt, 4),
                "recall": round(rec_dt, 4),
                "f1_score": round(f1_dt, 4)
            },
            "logistic_regression": {
                "accuracy": round(acc_lr, 4),
                "precision": round(prec_lr, 4),
                "recall": round(rec_lr, 4),
                "f1_score": round(f1_lr, 4)
            }
        },
        "feature_importances": importances,
        "tree_rules": tree_rules
    }

    with open(METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=4)
    print(f"Model metadata successfully saved to {METADATA_PATH}")


if __name__ == "__main__":
    train_and_evaluate()
