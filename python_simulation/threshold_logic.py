"""
threshold_logic.py
--------------------
Contains threshold values and decision logic for:
- Irrigation control (pump ON/OFF)
- Alert generation (low moisture, high temp, low water, etc.)

These thresholds can be tuned to match real sensor calibration.
"""

# ---- Threshold configuration ----
THRESHOLDS = {
    "soil_moisture_dry": 1500,     # below this => dry soil, pump ON
    "soil_moisture_wet": 2800,     # above this => sufficiently wet, pump OFF
    "temperature_high": 35.0,      # °C, triggers high temperature alert
    "humidity_low": 25.0,          # %, triggers low humidity alert
    "light_low": 300,              # ADC value, considered "dark"
    "water_level_low": 20.0,       # %, triggers low water level alert
}


def evaluate(reading, pump_state):
    """
    Evaluate sensor reading against thresholds.

    Args:
        reading (dict): sensor reading dict from SensorSimulator
        pump_state (bool): current pump state (True = ON)

    Returns:
        dict with:
            pump_state (bool): updated pump state
            alerts (list[str]): list of alert messages
    """
    alerts = []

    soil = reading["soil_moisture"]
    temp = reading["temperature"]
    hum = reading["humidity"]
    light = reading["light"]
    water = reading["water_level"]

    # --- Irrigation decision (with simple hysteresis) ---
    if soil < THRESHOLDS["soil_moisture_dry"]:
        pump_state = True
        alerts.append("LOW SOIL MOISTURE: Pump turned ON")
    elif soil > THRESHOLDS["soil_moisture_wet"]:
        pump_state = False

    # --- Temperature alert ---
    if temp > THRESHOLDS["temperature_high"]:
        alerts.append(f"HIGH TEMPERATURE ALERT: {temp}°C")

    # --- Humidity alert ---
    if hum < THRESHOLDS["humidity_low"]:
        alerts.append(f"LOW HUMIDITY ALERT: {hum}%")

    # --- Light alert (informational, e.g., for greenhouse lighting control) ---
    if light < THRESHOLDS["light_low"]:
        alerts.append(f"LOW LIGHT INTENSITY: {light} (consider grow-light ON)")

    # --- Water level alert ---
    if water < THRESHOLDS["water_level_low"]:
        alerts.append(f"LOW WATER LEVEL ALERT: {water}% (refill tank)")
        # Safety: don't run pump if tank is nearly empty
        if pump_state:
            alerts.append("PUMP SAFETY STOP: Water level too low")
            pump_state = False

    return {
        "pump_state": pump_state,
        "alerts": alerts,
    }
