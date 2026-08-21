"""
data_logger.py
----------------
Handles CSV data logging for sensor readings, pump status, and alerts.
"""

import csv
import os

CSV_HEADERS = [
    "timestamp",
    "soil_moisture",
    "temperature",
    "humidity",
    "light",
    "water_level",
    "pump_state",
    "alerts",
    "band_4_red",
    "band_8_nir",
    "ndvi",
    "crop_health",
    "ndvi_trend",
    "soil_condition",
    "crop_stress",
    "likely_cause",
    "stress_evidence",
    "crop_health_score",
]


class DataLogger:
    def __init__(self, filepath):
        self.filepath = filepath
        self._ensure_file()

    def _ensure_file(self):
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        
        # Keep existing observations safe if a future version changes the schema.
        # We never delete or overwrite a previous log automatically.
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r") as f:
                    reader = csv.reader(f)
                    existing_headers = next(reader)
                
                if existing_headers != CSV_HEADERS:
                    backup_path = self.filepath.replace(".csv", "_legacy.csv")
                    if not os.path.exists(backup_path):
                        os.rename(self.filepath, backup_path)
                        print(f"[Schema Migration] Previous log saved to {backup_path}. Creating fresh file.")
                    else:
                        raise RuntimeError(
                            f"Existing schema differs and backup already exists: {backup_path}. "
                            "Rename one of the files before running again."
                        )
            except (OSError, StopIteration, RuntimeError) as error:
                raise RuntimeError(
                    f"Unable to safely prepare sensor log '{self.filepath}': {error}"
                ) from error

        if not os.path.exists(self.filepath):
            with open(self.filepath, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(CSV_HEADERS)

    def log(self, reading, pump_state, alerts, sat_reading=None, stress_result=None):
        red = sat_reading["band_4_red"] if sat_reading else 0.0
        nir = sat_reading["band_8_nir"] if sat_reading else 0.0
        ndvi = sat_reading["ndvi"] if sat_reading else 0.0
        crop_health = sat_reading["crop_health"] if sat_reading else ""
        stress_result = stress_result or {}

        with open(self.filepath, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                reading["timestamp"],
                reading["soil_moisture"],
                reading["temperature"],
                reading["humidity"],
                reading["light"],
                reading["water_level"],
                "ON" if pump_state else "OFF",
                "; ".join(alerts) if alerts else "",
                red,
                nir,
                ndvi,
                crop_health,
                stress_result.get("ndvi_trend", 0.0),
                stress_result.get("soil_condition", ""),
                stress_result.get("crop_stress", ""),
                stress_result.get("likely_cause", ""),
                stress_result.get("stress_evidence", ""),
                stress_result.get("crop_health_score", 0.0),
            ])
