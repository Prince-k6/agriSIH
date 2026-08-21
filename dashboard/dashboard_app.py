"""
dashboard_app.py
------------------
Streamlit-based dashboard for the IoT-Enabled Smart Agriculture
Monitoring System. Reads logged sensor data (CSV) and displays:
- Live latest readings with status cards
- Historical trend charts
- Alert history table
- Pump ON/OFF timeline
- ML Model Diagnostics: training metrics, feature importances, and decision tree rules
"""

import os
import sys
import json
import pandas as pd
import streamlit as st

# Allow importing simulation modules
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "python_simulation"))

from threshold_logic import THRESHOLDS, evaluate  # noqa: E402
from ml_logic import evaluate_ml, MODEL_PATH  # noqa: E402

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "sensor_log.csv")
METADATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs", "model_metadata.json")

st.set_page_config(page_title="Smart Agriculture Dashboard", layout="wide")

st.title("🌱 IoT-Enabled Smart Agriculture Monitoring Dashboard")
st.caption("Simulated sensor data — Soil Moisture | Temperature | Humidity | Light | Water Level")

# ---- Sidebar Configuration ----
st.sidebar.header("Settings")

# Control Mode selection
control_mode = st.sidebar.radio(
    "Active Decision Logic Mode",
    ("Rules-Based (Thresholds)", "Machine Learning (Decision Tree)")
)
st.session_state["mode"] = "ml" if "Machine Learning" in control_mode else "rules"

# Check if ML model metadata exists
ml_metadata = None
if os.path.exists(METADATA_PATH):
    try:
        with open(METADATA_PATH, "r") as f:
            ml_metadata = json.load(f)
    except Exception as e:
        st.sidebar.error(f"Error loading model metadata: {e}")

if st.session_state["mode"] == "ml":
    if not ml_metadata:
        st.sidebar.warning("⚠️ ML Model is not trained yet. Run train_model.py in your console.")
    else:
        st.sidebar.success(f"🧠 ML Model Active\nTrained: {ml_metadata['trained_at']}")
        # Brief sidebar metrics
        st.sidebar.metric(
            "Model Accuracy", 
            f"{ml_metadata['metrics']['decision_tree']['accuracy'] * 100:.1f}%"
        )
        st.sidebar.metric(
            "Model F1-Score", 
            f"{ml_metadata['metrics']['decision_tree']['f1_score']:.4f}"
        )

# Main Navigation Tabs
tab1, tab2 = st.tabs(["🚜 Live Monitoring & Analytics", "🧠 ML Model Diagnostics"])

# Load CSV Data
if not os.path.exists(CSV_PATH):
    with tab1:
        st.warning(
            "No data found yet. Run the simulation first to populate the dashboard:\n\n"
            "`python main.py --mode rules --cycles 20 --interval 0.5`"
        )
    st.stop()

df = pd.read_csv(CSV_PATH)
if df.empty:
    with tab1:
        st.warning("Data file is empty. Run the simulation to generate readings.")
    st.stop()

df["timestamp"] = pd.to_datetime(df["timestamp"])
latest = df.iloc[-1]

# ---- TAB 1: Live Monitoring & Analytics ----
with tab1:
    st.subheader("📊 Latest Sensor Reading")
    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Soil Moisture", f"{latest['soil_moisture']:.0f}",
                 "Dry" if latest['soil_moisture'] < THRESHOLDS["soil_moisture_dry"] else "OK")
    col2.metric("Temperature", f"{latest['temperature']:.1f} °C",
                 "High" if latest['temperature'] > THRESHOLDS["temperature_high"] else "Normal")
    col3.metric("Humidity", f"{latest['humidity']:.1f} %",
                 "Low" if latest['humidity'] < THRESHOLDS["humidity_low"] else "Normal")
    col4.metric("Light Intensity", f"{latest['light']:.0f}",
                 "Low" if latest['light'] < THRESHOLDS["light_low"] else "Normal")
    col5.metric("Water Level", f"{latest['water_level']:.1f} %",
                 "Low" if latest['water_level'] < THRESHOLDS["water_level_low"] else "Normal")

    # Pump Status
    pump_color = "🟢 ON" if latest["pump_state"] == "ON" else "🔴 OFF"
    st.markdown(f"### 🚰 Pump Status: {pump_color}")

    # Alerts Display
    if isinstance(latest["alerts"], str) and latest["alerts"].strip():
        st.error(f"⚠️ {latest['alerts']}")
    else:
        st.success("✅ All parameters normal")

    # Dynamic Decision Engine Comparison
    latest_dict = {
        "timestamp": latest["timestamp"],
        "soil_moisture": latest["soil_moisture"],
        "temperature": latest["temperature"],
        "humidity": latest["humidity"],
        "light": latest["light"],
        "water_level": latest["water_level"],
    }
    
    rules_res = evaluate(latest_dict, pump_state=False)
    rules_pred = "ON" if rules_res["pump_state"] else "OFF"
    
    ml_pred = "N/A"
    ml_available = False
    if os.path.exists(MODEL_PATH):
        try:
            ml_res = evaluate_ml(latest_dict, current_pump_state=False)
            ml_pred = "ON" if ml_res["pump_state"] else "OFF"
            ml_available = True
        except Exception:
            pass

    with st.expander("🔍 Compare Decision Logic Predictions (Live)"):
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.write("#### 📝 Rules Engine Prediction")
            st.write(f"**Decision:** `{rules_pred}`")
            st.caption(f"Rule thresholds: Dry < {THRESHOLDS['soil_moisture_dry']} | Wet > {THRESHOLDS['soil_moisture_wet']}")
        with col_c2:
            st.write("#### 🧠 Machine Learning Prediction")
            if ml_available:
                st.write(f"**Decision:** `{ml_pred}`")
                st.caption("Based on trained Decision Tree model prediction.")
            else:
                st.write("**Decision:** `Model Not Trained`")
                st.caption("Run python_simulation/train_model.py to enable ML prediction.")

    st.divider()

    # Trend Charts
    st.subheader("📈 Sensor Trends")
    c1, c2 = st.columns(2)
    with c1:
        st.line_chart(df.set_index("timestamp")[["soil_moisture"]], height=250)
        st.line_chart(df.set_index("timestamp")[["temperature", "humidity"]], height=250)
    with c2:
        st.line_chart(df.set_index("timestamp")[["light"]], height=250)
        st.line_chart(df.set_index("timestamp")[["water_level"]], height=250)

    # Pump state timeline
    st.subheader("🚰 Pump State Timeline")
    pump_numeric = df["pump_state"].map({"ON": 1, "OFF": 0})
    st.area_chart(pd.DataFrame({"pump_on": pump_numeric.values}, index=df["timestamp"]), height=150)

    # Alerts Table
    st.subheader("🔔 Alert History")
    alert_df = df[df["alerts"].astype(str).str.strip() != ""][["timestamp", "alerts"]]
    if alert_df.empty:
        st.info("No alerts recorded yet.")
    else:
        st.dataframe(alert_df.iloc[::-1], use_container_width=True)

    # Raw Log
    with st.expander("📄 View Raw Sensor Log"):
        st.dataframe(df.iloc[::-1], use_container_width=True)

# ---- TAB 2: ML Model Diagnostics ----
with tab2:
    if not ml_metadata:
        st.warning("⚠️ Machine Learning model has not been trained yet.")
        st.info(
            "To train the ML models, run the training script in your terminal:\n\n"
            "```bash\n"
            "python python_simulation/train_model.py\n"
            "```\n"
            "This will create the model file and generate performance evaluation metrics."
        )
    else:
        st.subheader("🧠 Machine Learning Model Summary")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric("Primary Model", ml_metadata["model_type"])
        with col_m2:
            st.metric("Trained Timestamp", ml_metadata["trained_at"])

        st.divider()

        # Model comparison table
        st.subheader("📊 Classifier Performance Metrics (Test Set)")
        st.caption("Evaluating models on unseen test data split from simulated scenarios.")
        
        metrics_raw = ml_metadata["metrics"]
        formatted_metrics = []
        for model_name, metrics in metrics_raw.items():
            formatted_metrics.append({
                "Classifier": model_name.replace("_", " ").title(),
                "Accuracy": f"{metrics['accuracy'] * 100:.2f}%",
                "Precision": f"{metrics['precision'] * 100:.2f}%",
                "Recall": f"{metrics['recall'] * 100:.2f}%",
                "F1-Score": f"{metrics['f1_score']:.4f}",
            })
        
        st.dataframe(pd.DataFrame(formatted_metrics), use_container_width=True)
        
        st.divider()

        # Feature Importance Chart
        st.subheader("🎯 Feature Importance")
        st.caption("How heavily the Decision Tree relies on each sensor metric to predict irrigation need.")
        
        importances = ml_metadata["feature_importances"]
        imp_df = pd.DataFrame({
            "Sensor Feature": list(importances.keys()),
            "Relative Importance": list(importances.values())
        }).sort_values(by="Relative Importance", ascending=True)
        
        st.bar_chart(imp_df.set_index("Sensor Feature"), horizontal=True)

        st.divider()

        # Textual Decision Tree Rules
        st.subheader("🌳 Learned Decision Tree Structure")
        st.caption("This is the exact logical structure (the if/else boundaries) that the model learned automatically during training:")
        st.code(ml_metadata["tree_rules"], language="text")

