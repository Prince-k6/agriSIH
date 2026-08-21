"""
satellite_simulator.py
----------------------
Simulates Sentinel-2 multispectral satellite telemetry.
Specifically simulates Band 4 (Red) and Band 8 (NIR) reflectance,
calculates NDVI, and determines crop/vegetation health.
Includes scenarios where dry soil or hot weather causes plant stress,
resulting in leaf cellular degradation (lower NIR) and chlorophyll loss (higher Red),
which drives a drop in the NDVI value over time.
"""

import random

from ndvi import calculate_ndvi, classify_ndvi


class SatelliteSimulator:
    def __init__(self, scenario="normal"):
        """
        scenario: 'normal', 'dry_soil', 'hot_day', 'low_water', 'night'
        Sets baseline spectral reflectance values.
        """
        self.scenario = scenario
        
        # Base reflectance values (normalized between 0.0 and 1.0)
        # Healthy green vegetation reflects NIR (Band 8) heavily and absorbs Red (Band 4)
        self.red = 0.08  # ~8% reflectance
        self.nir = 0.72  # ~72% reflectance
        
        # Cumulative stress index to simulate progressive crop decay over cycles
        self.stress_cycles = 0

    def _drift(self, value, min_v, max_v, step):
        """Apply small random drift, clamped to range."""
        value += random.uniform(-step, step)
        return max(min_v, min(max_v, value))

    def read_all(self):
        """Generate simulated reflectance bands, calculate NDVI, and determine health."""
        
        # Progressive crop stress if scenario is dry soil or extremely hot day
        if self.scenario == "dry_soil":
            self.stress_cycles += 1
            # Red reflectance increases (loss of chlorophyll -> less absorption)
            # Max stress Red limit ~ 0.24
            self.red = self._drift(0.08 + (self.stress_cycles * 0.012), 0.05, 0.24, 0.005)
            # NIR reflectance decreases (leaf cell collapse -> less reflection)
            # Min stress NIR limit ~ 0.28
            self.nir = self._drift(0.72 - (self.stress_cycles * 0.024), 0.28, 0.76, 0.01)
            
        elif self.scenario == "hot_day":
            self.stress_cycles += 1
            self.red = self._drift(0.08 + (self.stress_cycles * 0.008), 0.05, 0.20, 0.005)
            self.nir = self._drift(0.72 - (self.stress_cycles * 0.016), 0.38, 0.76, 0.01)
            
        else:
            # Under normal, low_water, or night conditions, the crop remains healthy
            # with minor natural fluctuations (drift)
            self.red = self._drift(self.red, 0.06, 0.10, 0.003)
            self.nir = self._drift(self.nir, 0.68, 0.75, 0.005)
            # Slowly recover stress if returned to normal
            if self.stress_cycles > 0:
                self.stress_cycles -= 1

        ndvi = calculate_ndvi(self.red, self.nir)
        health_status, health_detail = classify_ndvi(ndvi)

        return {
            "band_4_red": round(self.red, 4),
            "band_8_nir": round(self.nir, 4),
            "ndvi": round(ndvi, 3),
            "crop_health": health_status,
            "health_detail": health_detail,
            "source": "Demo Sentinel-2-style reflectance",
        }


if __name__ == "__main__":
    # Test script
    print("Testing Satellite Simulator (Dry Soil scenario):")
    sat = SatelliteSimulator(scenario="dry_soil")
    for cycle in range(1, 11):
        print(f"Cycle {cycle}: {sat.read_all()}")
