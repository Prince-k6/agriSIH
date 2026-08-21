"""Phase 3: combine sensor and satellite signals into crop-stress evidence.

This is a transparent decision model, not a black-box classifier.  It is kept
separate from irrigation control: it explains the likely crop condition while
``threshold_logic.py`` remains responsible for the pump's safety decisions.
"""

from threshold_logic import THRESHOLDS


def calculate_ndvi_trend(ndvi_history):
    """Compare the latest NDVI with the oldest of up to five observations."""
    recent_values = ndvi_history[-5:]
    if len(recent_values) < 2:
        return 0.0
    return round(recent_values[-1] - recent_values[0], 3)


def soil_condition(soil_moisture):
    """Return a plain-language soil label based on existing pump thresholds."""
    if soil_moisture < THRESHOLDS["soil_moisture_dry"]:
        return "Dry"
    if soil_moisture > THRESHOLDS["soil_moisture_wet"]:
        return "Wet"
    return "Adequate"


def assess_crop_stress(reading, satellite_reading, ndvi_history):
    """Identify the most likely stress pattern from current fused evidence.

    The result is stored in the observation log and displayed in the Phase 3
    dashboard tab. It intentionally reports *likely* causes rather than making
    a diagnosis from limited data.
    """
    ndvi = satellite_reading["ndvi"]
    trend = calculate_ndvi_trend(ndvi_history)
    soil = reading["soil_moisture"]
    temperature = reading["temperature"]
    condition = soil_condition(soil)

    if soil < THRESHOLDS["soil_moisture_dry"] and (ndvi < 0.60 or trend <= -0.05):
        stress_level = "High"
        likely_cause = "Likely water stress"
        evidence = "Dry soil combined with weak or declining vegetation signal"
    elif soil < THRESHOLDS["soil_moisture_dry"]:
        stress_level = "Moderate"
        likely_cause = "Possible water stress"
        evidence = "Soil is dry; continue monitoring vegetation response"
    elif temperature > THRESHOLDS["temperature_high"] and trend <= -0.05:
        stress_level = "Moderate"
        likely_cause = "Possible heat stress"
        evidence = "High temperature combined with declining vegetation signal"
    elif ndvi < 0.30:
        stress_level = "High"
        likely_cause = "Low vegetation cover"
        evidence = "Very low NDVI; inspect crop cover and image quality"
    elif ndvi < 0.60 or trend <= -0.05:
        stress_level = "Moderate"
        likely_cause = "Vegetation needs observation"
        evidence = "NDVI is below the healthy range or declining"
    else:
        stress_level = "Low"
        likely_cause = "No clear stress pattern"
        evidence = "Soil and vegetation signals are currently within the expected range"

    return {
        "ndvi_trend": trend,
        "soil_condition": condition,
        "crop_stress": stress_level,
        "likely_cause": likely_cause,
        "stress_evidence": evidence,
        "crop_health_score": round(max(0, min(100, ndvi * 100)), 1),
    }
