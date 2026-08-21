# Phase 3: Sensor and Satellite Fusion

## Purpose

Phase 2 tells us whether the vegetation signal is healthy. Phase 3 combines
that signal with sensor readings so the system can state a **likely reason**
for crop stress.

```text
NDVI trend + soil moisture + temperature + humidity
                         ↓
          Explainable crop-stress assessment
                         ↓
    stress level + likely cause + supporting evidence
```

## Current decision rules

The project deliberately starts with visible decision rules instead of a complex
model. They are in `python_simulation/stress_analysis.py`.

| Evidence | Assessment |
| --- | --- |
| Dry soil only | Possible water stress |
| Dry soil + falling/weak NDVI | Likely water stress |
| High temperature + falling NDVI | Possible heat stress |
| Low or falling NDVI without a clear sensor cause | Vegetation needs observation |
| Healthy NDVI and acceptable soil | No clear stress pattern |

This wording is intentional. Sensor and satellite data can indicate a likely
pattern, but field inspection is still needed to confirm the cause.

## How data moves through the code

1. `main.py` obtains a sensor reading and a satellite reading each cycle.
2. It keeps a short NDVI history, so the project can detect direction—not only
   the latest value.
3. `assess_crop_stress()` combines the readings and returns simple fields such
   as `crop_stress`, `likely_cause`, and `stress_evidence`.
4. `data_logger.py` stores those fields in the same CSV observation.
5. The **Crop stress analysis** dashboard tab displays the result and the
   evidence used to create it.

## Demo command

```bash
python main.py --scenario dry_soil --cycles 8 --interval 0.2
streamlit run dashboard/dashboard_app.py
```

After several dry-soil cycles, the simulator produces both low soil moisture
and a falling NDVI trend. The dashboard should therefore show **Likely water
stress** with the supporting evidence.
