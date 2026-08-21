"""Judge-ready dashboard for the Smart Agriculture prototype.

Phase 2 remains deliberately explainable: Red + NIR -> NDVI -> vegetation
status. Current spectral readings are simulated; these columns are the hand-off
point for a future Sentinel-2 data connector.
"""

import json
import os
import sys

import pandas as pd
import streamlit as st

ROOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.append(os.path.join(ROOT_DIR, "python_simulation"))

from ml_logic import MODEL_PATH, evaluate_ml  # noqa: E402
from ndvi import classify_ndvi  # noqa: E402
from threshold_logic import THRESHOLDS, evaluate  # noqa: E402

CSV_PATH = os.path.join(ROOT_DIR, "data", "sensor_log.csv")
METADATA_PATH = os.path.join(ROOT_DIR, "outputs", "model_metadata.json")
SATELLITE_COLUMNS = {"band_4_red", "band_8_nir", "ndvi", "crop_health"}

st.set_page_config(
    page_title="AgriSense | Farm Intelligence",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown("""<style>
.stApp {background:#f5f7f2;color:#173d2d;}
[data-testid="stHeader"], [data-testid="stSidebar"], [data-testid="collapsedControl"] {display:none;}
.block-container {padding:1.4rem 3rem 2.5rem; max-width:1500px;}
.appbar {display:flex; justify-content:space-between; align-items:center; background:#ffffff; border:1px solid #e2e9df; border-radius:16px; padding:1rem 1.35rem; margin-bottom:1.25rem; box-shadow:0 5px 16px rgba(31,68,43,.05);}
.brand {font-size:1.65rem; font-weight:750; color:#124633; margin:0;}.brand span {color:#6d9c3a;}.subbrand {color:#718176; margin:.15rem 0 0; font-size:.92rem;}.live-pill {background:#e6f5e7; color:#18733d; border-radius:999px; padding:.45rem .75rem; font-size:.82rem; font-weight:700;}
.section-card{background:#fff;border:1px solid #e2e9df;border-radius:14px;padding:1.1rem 1.2rem;min-height:118px;}.section-card h4{margin:0 0 .45rem;color:#174633;}.section-card p{margin:0;color:#587064;}div[data-testid="stMetric"]{background:#fff;border:1px solid #e2e9df;border-radius:12px;padding:.75rem;}.status-panel{background:#173f2e;color:#fff;border-radius:15px;padding:1.25rem 1.4rem;}.status-panel h3{margin:0 0 .35rem;color:#fff;}.status-panel p{margin:0;color:#d6ead8;}.small-label{color:#718176;font-size:.78rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;}
</style>""", unsafe_allow_html=True)


def load_data():
    if not os.path.exists(CSV_PATH):
        return pd.DataFrame()
    data = pd.read_csv(CSV_PATH)
    if not data.empty:
        data["timestamp"] = pd.to_datetime(data["timestamp"], errors="coerce")
        data = data.dropna(subset=["timestamp"])
    return data


def load_metadata():
    if not os.path.exists(METADATA_PATH):
        return None
    try:
        with open(METADATA_PATH, "r") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError):
        return None


def value(row, name, default=0.0):
    item = row.get(name, default)
    return default if pd.isna(item) else item


def ndvi_delta(data):
    if "ndvi" not in data.columns or len(data) < 2:
        return None
    return round(float(data["ndvi"].iloc[-1]) - float(data["ndvi"].iloc[-2]), 3)


def recommendations(latest, has_satellite):
    messages = []
    soil, water, ndvi = value(latest, "soil_moisture"), value(latest, "water_level"), value(latest, "ndvi")
    if water < THRESHOLDS["water_level_low"]:
        messages.append(("Critical", "Refill the water tank before irrigating. Pump protection is active."))
    if soil < THRESHOLDS["soil_moisture_dry"] and has_satellite and ndvi < 0.60:
        messages.append(("Priority", "Possible water stress: soil is dry and vegetation health is declining. Inspect and irrigate this zone."))
    elif soil < THRESHOLDS["soil_moisture_dry"]:
        messages.append(("Priority", "Soil is dry. Start or verify irrigation, subject to the tank-level safety check."))
    if has_satellite and ndvi < 0.30:
        messages.append(("Inspect", "Low vegetation signal. Check for bare soil, crop loss, disease, or cloud-contaminated satellite pixels."))
    return messages or [("Good", "No immediate irrigation or crop-health issue detected. Continue routine monitoring.")]


data, metadata = load_data(), load_metadata()
st.markdown("""<div class='appbar'>
<div><p class='brand'>🌾 Agri<span>Sense</span></p><p class='subbrand'>Farm monitoring and crop-stress intelligence</p></div>
<div class='live-pill'>● LIVE SIMULATION</div>
</div>""", unsafe_allow_html=True)

if data.empty:
    st.warning("No observations found. Run `python main.py --cycles 12` from the project root, then refresh this page.")
    st.stop()

latest = data.iloc[-1]
has_satellite = SATELLITE_COLUMNS.issubset(data.columns)
tabs = st.tabs(["Overview", "Crop health", "Soil & weather", "Insights", "Data"])

with tabs[0]:
    st.markdown("## Field overview")
    soil, temperature = value(latest, "soil_moisture"), value(latest, "temperature")
    humidity, water = value(latest, "humidity"), value(latest, "water_level")
    health_status = classify_ndvi(value(latest, "ndvi"))[0] if has_satellite else "Pending"
    change = ndvi_delta(data) if has_satellite else None
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Soil moisture", f"{soil:.0f}", "Dry" if soil < THRESHOLDS["soil_moisture_dry"] else "Within range")
    c2.metric("Temperature", f"{temperature:.1f} °C", "High" if temperature > THRESHOLDS["temperature_high"] else "Normal")
    c3.metric("Humidity", f"{humidity:.1f} %", "Low" if humidity < THRESHOLDS["humidity_low"] else "Normal")
    c4.metric("Tank level", f"{water:.0f} %", "Refill" if water < THRESHOLDS["water_level_low"] else "Available")
    c5.metric("Vegetation health", health_status, f"NDVI change {change:+.3f}" if change is not None else "Awaiting satellite signal")
    if "crop_stress" in data.columns:
        st.markdown(f"<p class='small-label'>Current crop assessment</p><h3>{value(latest, 'crop_stress', 'Pending')} risk · {value(latest, 'likely_cause', 'Awaiting analysis')}</h3>", unsafe_allow_html=True)
    left, right = st.columns([1.15, 1])
    with left:
        st.markdown("### Priority action")
        for priority, message in recommendations(latest, has_satellite):
            getattr(st, {"Good": "success", "Priority": "warning", "Inspect": "error", "Critical": "error"}[priority])(f"**{priority}:** {message}")
    with right:
        st.markdown("### Irrigation")
        pump = str(value(latest, "pump_state", "OFF"))
        st.metric("Pump", "ON" if pump == "ON" else "OFF")
        alerts = str(value(latest, "alerts", "")).strip()
        st.caption(alerts if alerts and alerts.lower() != "nan" else "No active sensor alerts.")
    st.markdown("### Field conditions over time")
    columns = [column for column in ["soil_moisture", "temperature", "humidity", "water_level"] if column in data]
    st.line_chart(data.set_index("timestamp")[columns], height=260)

with tabs[1]:
    st.markdown("## Crop health")
    if not has_satellite:
        st.info("Generate new readings with `python main.py` to add Band 4, Band 8, and NDVI observations.")
    else:
        red, nir, ndvi = value(latest, "band_4_red"), value(latest, "band_8_nir"), value(latest, "ndvi")
        status, detail = classify_ndvi(ndvi)
        a, b, c, d = st.columns(4)
        a.metric("Band 4 · Red", f"{red:.4f}", "Chlorophyll absorption")
        b.metric("Band 8 · NIR", f"{nir:.4f}", "Leaf structure reflection")
        c.metric("NDVI", f"{ndvi:.3f}", "Range: −1 to +1")
        d.metric("Vegetation status", status, detail)
        st.latex(r"NDVI = \frac{NIR - Red}{NIR + Red}")
        st.markdown("### NDVI trend")
        st.line_chart(data.set_index("timestamp")[["ndvi"]], height=260)

with tabs[2]:
    st.markdown("## Soil & weather")
    required_columns = {"ndvi_trend", "soil_condition", "crop_stress", "likely_cause", "stress_evidence", "crop_health_score"}
    if not required_columns.issubset(data.columns):
        st.info("Run `python main.py --scenario dry_soil --cycles 8` to generate Phase 3 fused observations.")
    else:
        stress, cause = value(latest, "crop_stress", "Pending"), value(latest, "likely_cause", "Pending")
        evidence = value(latest, "stress_evidence", "Pending")
        score = value(latest, "crop_health_score")
        trend = value(latest, "ndvi_trend")
        a, b, c, d = st.columns(4)
        a.metric("Crop health score", f"{score:.0f}/100", "Based on latest NDVI")
        b.metric("Stress level", stress)
        c.metric("Likely cause", cause)
        d.metric("NDVI trend", f"{trend:+.3f}", "Last 5 observations")
        st.markdown("### Current crop-stress signal")
        if stress == "High":
            st.error(f"**{cause}:** {evidence}")
        elif stress == "Moderate":
            st.warning(f"**{cause}:** {evidence}")
        else:
            st.success(f"**{cause}:** {evidence}")
        evidence_table = pd.DataFrame([{
            "Soil condition": value(latest, "soil_condition", "Pending"),
            "Soil moisture": f"{value(latest, 'soil_moisture'):.0f}",
            "Temperature": f"{value(latest, 'temperature'):.1f} °C",
            "Humidity": f"{value(latest, 'humidity'):.1f}%",
            "NDVI": f"{value(latest, 'ndvi'):.3f}",
            "NDVI trend": f"{trend:+.3f}",
        }])
        st.dataframe(evidence_table, width="stretch", hide_index=True)

with tabs[3]:
    st.markdown("## Insights")
    latest_dict = {name: value(latest, name) for name in ["soil_moisture", "temperature", "humidity", "light", "water_level"]}
    rules_result = evaluate(latest_dict, pump_state=False)
    c1, c2 = st.columns(2)
    c1.markdown("### Irrigation decision")
    c1.metric("Irrigation decision", "ON" if rules_result["pump_state"] else "OFF")
    c1.write(f"Dry-soil trigger: below `{THRESHOLDS['soil_moisture_dry']}` · tank safety threshold: `{THRESHOLDS['water_level_low']}%`.")
    c1.caption("; ".join(rules_result["alerts"]) or "No rule alert for this observation.")
    c2.markdown("### Model check")
    if os.path.exists(MODEL_PATH):
        try:
            result = evaluate_ml(latest_dict, current_pump_state=False)
            c2.metric("Decision Tree prediction", "ON" if result["pump_state"] else "OFF")
            c2.caption("; ".join(result["alerts"]) or "No ML-generated alert.")
        except Exception as error:
            c2.warning(f"Model could not be evaluated: {error}")
    else:
        c2.info("Train the baseline model to view its prediction.")

with tabs[4]:
    st.markdown("## Farm data")
    c1, c2 = st.columns([1, 1.2])
    with c1:
        st.metric("Logged observations", len(data))
        st.metric("Latest reading", latest["timestamp"].strftime("%d %b %Y, %H:%M:%S"))
        st.download_button("Download observation log", data.to_csv(index=False), "farm_observations.csv", "text/csv")
    with c2:
        if metadata:
            metrics = metadata.get("metrics", {}).get("decision_tree", {})
            st.metric("Decision Tree test accuracy", f"{metrics.get('accuracy', 0) * 100:.1f}%")
            st.caption(f"Trained: {metadata.get('trained_at', 'unknown')} · Features: {', '.join(metadata.get('features', []))}")
        else:
            st.info("Run `python python_simulation/train_model.py` to produce the baseline-model evidence.")
    with st.expander("View latest raw observations"):
        st.dataframe(data.iloc[::-1], width="stretch")
