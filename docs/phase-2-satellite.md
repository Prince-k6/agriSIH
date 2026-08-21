# Phase 2: Satellite and Multispectral Monitoring

## What this phase demonstrates

This prototype adds an understandable satellite-data path alongside the existing
sensor path:

```text
Sentinel-2-style Band 4 (Red) + Band 8 (NIR)
                 ↓
                NDVI
                 ↓
       Vegetation-health signal
                 ↓
      Dashboard and future sensor fusion
```

The current project uses controlled simulated reflectance. This lets the team
demonstrate the complete calculation and UI without claiming that it is live
satellite data. Replacing the simulator with a Sentinel-2 data downloader is a
future ingestion task; its output must provide the same `band_4_red` and
`band_8_nir` fields.

## Sentinel-2 in plain language

Sentinel-2 is a European Earth-observation mission that captures the same
location in multiple wavelength bands. Different surfaces reflect different
amounts of light at those wavelengths.

- **Band 4 (Red):** healthy leaves absorb red light for photosynthesis.
- **Band 8 (Near Infrared / NIR):** healthy leaf cell structures strongly
  reflect near-infrared light, which people cannot see.

## NDVI calculation

```text
NDVI = (NIR - Red) / (NIR + Red)
```

NDVI ranges from -1 to +1. In this prototype:

| NDVI | Status | Meaning |
| --- | --- | --- |
| >= 0.60 | Healthy | Dense, active vegetation |
| 0.30–0.59 | Watch | Moderate vegetation or early stress |
| < 0.30 | Critical | Sparse vegetation or significant stress |

NDVI is an early vegetation signal, not a diagnosis. Clouds, bare soil, crop
growth stage, and field boundaries can affect it. The Phase 3 goal is to pair
an NDVI trend with soil moisture, temperature, and humidity to identify likely
causes such as water stress.

## Code map

| File | Responsibility |
| --- | --- |
| `python_simulation/satellite_simulator.py` | Produces understandable demo Red/NIR readings for each scenario. |
| `python_simulation/ndvi.py` | Calculates and classifies NDVI. |
| `main.py` | Joins sensor and satellite readings and writes one observation. |
| `python_simulation/data_logger.py` | Stores sensor, Red, NIR, NDVI, and health fields in one CSV. |
| `dashboard/dashboard_app.py` | Presents the satellite evidence and its connection to sensor decisions. |

## Demonstration commands

```bash
# A normal field stays healthy.
python main.py --scenario normal --cycles 8 --interval 0.2

# Dry soil produces a declining NDVI signal over repeated observations.
python main.py --scenario dry_soil --cycles 12 --interval 0.2

streamlit run dashboard/dashboard_app.py
```

For a live Sentinel-2 implementation, acquire cloud-filtered B04 and B08
pixels for the same field and date, calculate NDVI per pixel with the same
formula, and log a field/zone summary in this schema.
