"""
sensor_simulator.py
--------------------
Simulates readings from soil moisture, temperature, humidity,
light intensity, and water level sensors for the
IoT-Enabled Smart Agriculture Monitoring System.

No real hardware is required — values are generated using
randomized models that mimic real sensor behavior, including
drift and occasional spikes (dry soil, heatwave, low water, etc.)
"""

import random
import time


class SensorSimulator:
    def __init__(self, scenario="normal"):
        """
        scenario: 'normal', 'dry_soil', 'hot_day', 'low_water', 'night'
        Controls which simulated condition is generated.
        """
        self.scenario = scenario

        # base values
        self.soil_moisture = 2500   # ADC-like value (0-4095), higher = wetter
        self.temperature = 28.0     # Celsius
        self.humidity = 55.0        # %
        self.light = 1800           # ADC-like value (0-4095), higher = brighter
        self.water_level = 80.0     # % of tank

    def _drift(self, value, min_v, max_v, step):
        """Apply small random drift, clamped to range."""
        value += random.uniform(-step, step)
        return max(min_v, min(max_v, value))

    def read_all(self):
        """Generate one set of sensor readings based on the scenario."""

        if self.scenario == "dry_soil":
            self.soil_moisture = self._drift(self.soil_moisture, 200, 4095, 80)
            self.soil_moisture = min(self.soil_moisture, 1400)  # force dry
        elif self.scenario == "hot_day":
            self.temperature = self._drift(self.temperature, 20, 45, 1.0)
            self.temperature = max(self.temperature, 36)
            self.humidity = self._drift(self.humidity, 10, 100, 1.5)
        elif self.scenario == "low_water":
            self.water_level = self._drift(self.water_level, 0, 100, 3)
            self.water_level = min(self.water_level, 15)
        elif self.scenario == "night":
            self.light = self._drift(self.light, 0, 4095, 50)
            self.light = min(self.light, 300)
        else:  # normal
            self.soil_moisture = self._drift(self.soil_moisture, 200, 4095, 60)
            self.temperature = self._drift(self.temperature, 15, 40, 0.6)
            self.humidity = self._drift(self.humidity, 20, 95, 1.2)
            self.light = self._drift(self.light, 0, 4095, 100)
            self.water_level = self._drift(self.water_level, 0, 100, 1.0)

        return {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "soil_moisture": round(self.soil_moisture, 1),
            "temperature": round(self.temperature, 2),
            "humidity": round(self.humidity, 2),
            "light": round(self.light, 1),
            "water_level": round(self.water_level, 2),
        }


if __name__ == "__main__":
    sim = SensorSimulator(scenario="normal")
    for _ in range(5):
        print(sim.read_all())
        time.sleep(0.2)
