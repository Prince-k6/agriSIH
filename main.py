"""
main.py
--------
Entry point for the IoT-Enabled Smart Agriculture Monitoring System
(Python simulation mode — no real hardware required).

This script:
1. Generates simulated sensor readings (soil moisture, temperature,
   humidity, light intensity, water level)
2. Applies threshold-based decision logic (irrigation + alerts)
3. Prints a live "serial monitor" style output to the console
4. Logs all data to data/sensor_log.csv

Run:
    python main.py
    python main.py --scenario dry_soil
    python main.py --cycles 20 --interval 1
"""

import argparse
import time
import sys
import os

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "python_simulation"))

from sensor_simulator import SensorSimulator
from satellite_simulator import SatelliteSimulator
from stress_analysis import assess_crop_stress
from threshold_logic import evaluate
from ml_logic import evaluate_ml
from data_logger import DataLogger


def main():
    parser = argparse.ArgumentParser(
        description="IoT Smart Agriculture Monitoring System - Python Simulation"
    )
    parser.add_argument(
        "--scenario",
        choices=["normal", "dry_soil", "hot_day", "low_water", "night"],
        default="normal",
        help="Simulation scenario to generate sensor data",
    )
    parser.add_argument(
        "--cycles", type=int, default=10, help="Number of sensor read cycles"
    )
    parser.add_argument(
        "--interval", type=float, default=1.0, help="Seconds between cycles"
    )
    parser.add_argument(
        "--mode",
        choices=["rules", "ml"],
        default="rules",
        help="Decision making mode: rules (threshold-based) or ml (machine learning classifier)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print(" IoT-Enabled Smart Agriculture Monitoring System")
    print(" Mode: Python Simulation (No Hardware Required)")
    print(f" Scenario: {args.scenario}")
    print(f" Decision Logic: {args.mode.upper()}")
    print("=" * 60)

    sim = SensorSimulator(scenario=args.scenario)
    sat_sim = SatelliteSimulator(scenario=args.scenario)

    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    log_path = os.path.join(data_dir, "sensor_log.csv")
    logger = DataLogger(log_path)

    pump_state = False
    ndvi_history = []

    for cycle in range(1, args.cycles + 1):
        reading = sim.read_all()
        sat_reading = sat_sim.read_all()
        ndvi_history.append(sat_reading["ndvi"])
        stress_result = assess_crop_stress(reading, sat_reading, ndvi_history)
        
        if args.mode == "ml":
            try:
                result = evaluate_ml(reading, pump_state)
            except FileNotFoundError as e:
                print(f"\n[Warning] {e}")
                print("Falling back to RULES mode for this cycle...")
                result = evaluate(reading, pump_state)
        else:
            result = evaluate(reading, pump_state)
            
        pump_state = result["pump_state"]
        alerts = result["alerts"]

        # --- Serial-monitor style output ---
        print(f"\n[Cycle {cycle}/{args.cycles}] {reading['timestamp']}")
        print(f"  Soil Moisture : {reading['soil_moisture']}")
        print(f"  Temperature   : {reading['temperature']} C")
        print(f"  Humidity      : {reading['humidity']} %")
        print(f"  Light         : {reading['light']}")
        print(f"  Water Level   : {reading['water_level']} %")
        print(f"  Satellite NDVI: {sat_reading['ndvi']} ({sat_reading['crop_health']})")
        print(f"  Spectral Bands: Red={sat_reading['band_4_red']}, NIR={sat_reading['band_8_nir']}")
        print(f"  Crop Stress   : {stress_result['crop_stress']} — {stress_result['likely_cause']}")
        print(f"  Evidence      : {stress_result['stress_evidence']}")
        print(f"  Pump Status   : {'ON' if pump_state else 'OFF'}")

        if alerts:
            for alert in alerts:
                print(f"  >> ALERT: {alert}")
        else:
            print("  >> Status: Normal - no alerts")

        logger.log(reading, pump_state, alerts, sat_reading, stress_result)

        if cycle < args.cycles:
            time.sleep(args.interval)

    print("\n" + "=" * 60)
    print(f" Simulation complete. Data logged to: {log_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
