# System Architecture

## Text-Based Architecture Diagram

```
        ┌────────────────────────┐
        │        SENSORS          │
        │  - Soil Moisture (AO)   │
        │  - DHT22 (Temp/Humidity)│
        │  - LDR (Light)          │
        │  - Water Level Sensor   │
        └───────────┬─────────────┘
                     │ Analog/Digital signals
                     ▼
        ┌────────────────────────┐
        │   ESP32 Microcontroller │
        │  (or Python Simulation) │
        │  - Reads sensor values  │
        │  - Threshold checking   │
        │  - Irrigation decision  │
        └───────────┬─────────────┘
                     │ MQTT / Serial / CSV
                     ▼
        ┌────────────────────────┐
        │   Data Processing &     │
        │   Logging Layer         │
        │  - data_logger.py       │
        │  - sensor_log.csv       │
        └───────────┬─────────────┘
                     │
        ┌────────────┴─────────────┐
        ▼                           ▼
┌──────────────────┐      ┌──────────────────────┐
│   Dashboard       │      │   Alert System        │
│ (Streamlit /      │      │ - Low soil moisture   │
│  ThingSpeak /     │      │ - High temperature    │
│  Blynk / Node-RED)│      │ - Low humidity        │
└──────────────────┘      │ - Low water level     │
                           └──────────┬────────────┘
                                       ▼
                           ┌──────────────────────┐
                           │  Actuator (Relay/Pump)│
                           │  ON / OFF control     │
                           └──────────────────────┘
```

## Data Flow

```
Sensor Data → Microcontroller / Simulation → Data Processing
   → Threshold Checking → Dashboard Update → Alert Generation
   → Irrigation Decision (Pump ON/OFF)
```

## Hardware / Software Flow

1. **Sensors** capture environmental data (soil moisture, temperature,
   humidity, light, water level).
2. **ESP32 / Python simulation** reads raw values from sensors.
3. **Threshold logic** (`threshold_logic.py`) compares readings against
   configured limits.
4. **Decision engine** decides pump ON/OFF and generates alert messages.
5. **Data logger** (`data_logger.py`) writes readings, pump state, and
   alerts to `data/sensor_log.csv`.
6. **Dashboard** (`dashboard/dashboard_app.py`, Streamlit) reads the CSV
   and visualizes trends, current status, and alert history.
7. Optional: data can also be pushed to **ThingSpeak**, **Blynk**, or
   **Node-RED** via MQTT/HTTP for cloud-based dashboards.
