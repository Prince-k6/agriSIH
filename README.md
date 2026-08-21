# IoT-Enabled Smart Agriculture Monitoring System

This project is a smart irrigation prototype for monitoring agricultural
conditions and deciding when a water pump should run. It supports a complete
Python simulation, a Streamlit dashboard, machine-learning diagnostics, and
an optional ESP32 implementation.

## What the Project Does

The system generates or reads five environmental measurements:

- Soil moisture
- Temperature
- Humidity
- Light intensity
- Water-tank level

The decision engine uses the measurements to:

- Turn the irrigation pump ON or OFF
- Detect conditions such as dry soil, high temperature, low humidity, low
	light, and low water level
- Record every reading, pump state, and alert in `data/sensor_log.csv`

The project has two decision modes:

- **Rules mode:** Uses configured thresholds and is available immediately.
- **ML mode:** Uses a trained Decision Tree classifier. A Logistic Regression
	model is also trained for comparison.

## Project Structure

```text
main.py                         Python simulation entry point
requirements.txt                Python dependencies
python_simulation/              Simulator, rules, logger, and ML scripts
dashboard/dashboard_app.py     Streamlit monitoring dashboard
data/                           Sensor logs and training data
outputs/                        Trained model and model metadata
arduino_code/                   ESP32 and MQTT implementation
circuit_diagram/                Wokwi circuit configuration
docs/architecture.md            System architecture and data flow
```

## Requirements

- Python 3.9 or newer
- `pip`
- macOS, Linux, or Windows

Real hardware is not required for the Python simulation or dashboard.

## Setup

From the project root, create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Run the Simulation

Run the default simulation. It generates 10 readings at one-second intervals
and appends them to `data/sensor_log.csv`:

```bash
python main.py
```

Useful examples:

```bash
# Simulate dry soil for 20 cycles, with half a second between readings
python main.py --scenario dry_soil --cycles 20 --interval 0.5

# Test other scenarios: normal, hot_day, low_water, or night
python main.py --scenario hot_day --cycles 10

# Run the simulation with the trained ML model
python main.py --mode ml --cycles 20 --interval 0.5
```

Available options:

```text
--scenario   normal | dry_soil | hot_day | low_water | night
--cycles     Number of readings to generate (default: 10)
--interval   Seconds between readings (default: 1.0)
--mode       rules | ml (default: rules)
```

## Train the ML Model

The training script creates a fresh synthetic dataset of 1,200 records, trains
Decision Tree and Logistic Regression classifiers, evaluates both models, and
saves the Decision Tree used by the application:

```bash
python python_simulation/train_model.py
```

Generated files:

- `data/training_data.csv`
- `outputs/irrigation_model.pkl`
- `outputs/model_metadata.json`

Run training before using `--mode ml`. If the model is unavailable, `main.py`
falls back to rules mode for that cycle.

## Start the Dashboard

First generate sensor data if `data/sensor_log.csv` is empty:

```bash
python main.py --cycles 20 --interval 0.5
```

Start the Streamlit dashboard from the project root:

```bash
streamlit run dashboard/dashboard_app.py
```

Open the local URL shown by Streamlit, usually `http://localhost:8501`.
The dashboard displays the latest readings, sensor trends, pump history,
alerts, raw log data, and ML model diagnostics. Use the sidebar to switch
between rules-based and ML decision modes.

## Optional ESP32 Version

The Arduino sketch in `arduino_code/smart_agriculture_esp32.ino` reads a DHT22,
soil-moisture sensor, and LDR, controls a relay-based pump, and publishes JSON
sensor data over MQTT. It is also intended to work in the Wokwi simulator.

To use it:

1. Open the sketch in Arduino IDE or create an ESP32 project in Wokwi.
2. Install the ESP32 board package and the `DHT sensor library` and
	 `PubSubClient` libraries.
3. Connect the sensors and relay using the pin definitions in the sketch.
4. Upload the sketch or start the Wokwi simulation.
5. Open the Serial Monitor at `115200` baud.

The sketch uses the public MQTT broker `broker.hivemq.com` and publishes to
the topic `farm/node1/data`. Use a private broker for production deployments.

## Data Flow

```text
Sensors or simulator
				-> threshold or ML decision engine
				-> pump state and alerts
				-> CSV logger
				-> Streamlit dashboard
```

For the detailed architecture, see [docs/architecture.md](docs/architecture.md).

## Troubleshooting

**`ModuleNotFoundError`**

Activate `.venv` and install the requirements again:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
```

**Dashboard says no data is available**

Run `python main.py --cycles 20` and refresh the dashboard.

**ML mode says the model is missing**

Run `python python_simulation/train_model.py` first.
