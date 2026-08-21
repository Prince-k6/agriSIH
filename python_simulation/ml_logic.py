"""
ml_logic.py
-----------
Contains decision logic utilizing the trained Machine Learning model.
It loads the serialized model and performs predictions while enforcing
hardware safety constraints (e.g. pump safety stop if water is low).
"""

import os
import pickle
import sys
import pandas as pd

# Load thresholds for environmental alerts and safety stops
from threshold_logic import THRESHOLDS

MODEL_CACHE = None
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs", "irrigation_model.pkl")


def load_model(model_path=MODEL_PATH):
    """Load the machine learning model from disk, caching it in memory."""
    global MODEL_CACHE
    if MODEL_CACHE is not None:
        return MODEL_CACHE

    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Trained model not found at '{model_path}'. "
            "Please train the model first by running: python python_simulation/train_model.py"
        )

    with open(model_path, "rb") as f:
        MODEL_CACHE = pickle.load(f)
    return MODEL_CACHE


def evaluate_ml(reading, current_pump_state, model_path=MODEL_PATH):
    """
    Evaluate sensor readings using the trained machine learning model.
    Applies the same environmental warnings and safety stops as the rules engine.

    Args:
        reading (dict): current sensor readings
        current_pump_state (bool): state before this cycle
        model_path (str): path to the saved model

    Returns:
        dict: containing:
            pump_state (bool): updated pump state
            alerts (list[str]): list of alert and status messages
    """
    alerts = []
    
    # 1. Load the model
    try:
        model = load_model(model_path)
    except FileNotFoundError as e:
        # If model is not trained, raise to let main.py know
        raise e

    # 2. Prep features for prediction (features must be in correct order)
    features = ["soil_moisture", "temperature", "humidity", "light", "water_level"]
    X = pd.DataFrame([reading])[features]

    # 3. Predict pump state using the ML model
    ml_pred = int(model.predict(X)[0])  # 0 or 1
    new_pump_state = True if ml_pred == 1 else False

    # 4. Generate alerts and enforce safety constraints
    temp = reading["temperature"]
    hum = reading["humidity"]
    light = reading["light"]
    water = reading["water_level"]

    # If ML predicted ON, log it
    if new_pump_state and not current_pump_state:
        alerts.append("[ML DECISION] Soil dry: Pump turned ON")
    elif not new_pump_state and current_pump_state:
        # Soil became sufficiently wet or other conditions met
        pass

    # --- Environmental warnings (same as baseline rule logic) ---
    if temp > THRESHOLDS["temperature_high"]:
        alerts.append(f"HIGH TEMPERATURE ALERT: {temp}°C")

    if hum < THRESHOLDS["humidity_low"]:
        alerts.append(f"LOW HUMIDITY ALERT: {hum}%")

    if light < THRESHOLDS["light_low"]:
        alerts.append(f"LOW LIGHT INTENSITY: {light} (consider grow-light ON)")

    if water < THRESHOLDS["water_level_low"]:
        alerts.append(f"LOW WATER LEVEL ALERT: {water}% (refill tank)")
        # Critical Safety Stop: Force pump OFF if water tank is too low
        if new_pump_state:
            alerts.append("[ML SAFETY OVERRIDE] PUMP SAFETY STOP: Water level too low")
            new_pump_state = False

    return {
        "pump_state": new_pump_state,
        "alerts": alerts,
    }
