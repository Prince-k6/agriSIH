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
]


class DataLogger:
    def __init__(self, filepath):
        self.filepath = filepath
        self._ensure_file()

    def _ensure_file(self):
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        if not os.path.exists(self.filepath):
            with open(self.filepath, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(CSV_HEADERS)

    def log(self, reading, pump_state, alerts):
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
            ])
