# Contents
- **Unified Event Schema** (input data from sensors/telemetry)
- **Actuator Command Schema** (output data to actuators)

# Unified Event Schema

For internal sensor and telemetry data

```json
{
  "timestamp": "2036-03-06T10:42:10Z",
  "source_id": "string",
  "source_type": "rest | telemetry",
  "status": "ok | warning | unknown",
  "metrics": [
    {
      "name": "string",
      "value": 0.0,
      "unit": "string"
    }
  ]
}
```

## General Normalization Policy
All incoming payloads from REST sensors and telemetry streams are converted into a unified internal event schema to ensure consistent processing across the system.

Each payload generates one normalized event. The timestamp is derived from the original message, the source identifier corresponds to the sensor or topic name, and the source type indicates whether the data comes from REST polling or telemetry streaming. 

All numeric observations are mapped into the metrics array, while contextual non-numeric attributes may be preserved in metadata. This approach allows the rule engine, state cache, and dashboard to operate on a consistent data format regardless of the original device schema.

## Normalization Rules

### Rest Sensors

#### `rest.scalar.v1`

- `timestamp` ← `captured_at`
- `source_id` ← `sensor_id`
- `source_type` ← `"rest"`
- `status` ← `status`
- `metrics` contains one entry:
    - `name` ← `metric`
    - `value` ← `value`
    - `unit` ← `unit`

- Example:

    1.
        ```json
        {
            "sensor_id": "greenhouse_temperature",
            "captured_at": "2036-03-06T10:42:10Z",
            "metric": "temperature",
            "value": 27.4,
            "unit": "C",
            "status": "ok"
        }
        ```
        →
        ```json
        {
            "timestamp": "2036-03-06T10:42:10Z",
            "source_id": "greenhouse_temperature",
            "source_type": "rest",
            "status": "ok",
            "metrics": [
                {"name": "temperature", "value": 27.4, "unit": "C"}
            ]
        }
        ```
    1.
        ```json
        {
            "sensor_id": "greenhouse_temperature",
            "captured_at": "2036-03-06T10:42:10Z",
            "metric": "temperature",
            "value": 27.4,
            "unit": "C",
            "status": "ok"
        }
        ```

- Examples:
    1. `rest.particulate.v1`
        ```json
        {
            "sensor_id": "air_quality_pm25",
            "captured_at": "2036-03-06T10:00:00Z",
            "pm1_ug_m3": 5.2,
            "pm25_ug_m3": 12.5,
            "pm10_ug_m3": 18.1,
            "status": "warning"
        }
        ```
        →
        ```json
        {
            "timestamp": "2036-03-06T10:00:00Z",
            "source_id": "air_quality_pm25",
            "source_type": "rest_sensor",
            "status": "warning",
            "metrics": [
                {"name": "pm1", "value": 5.2, "unit": "ug_m3"},
                {"name": "pm25", "value": 12.5, "unit": "ug_m3"},
                {"name": "pm10", "value": 18.1, "unit": "ug_m3"}
            ]
        }
        ```

    2. `topic.power.v1`
        ```json
        {
            "topic": "mars/telemetry/solar_array",
            "event_time": "2036-03-06T10:01:00Z",
            "subsystem": "Panel_A",
            "power_kw": 15.5,
            "voltage_v": 120.0,
            "current_a": 129.1,
            "cumulative_kwh": 5040.2
        }
        ```
        →
        ```json
        {
            "timestamp": "2036-03-06T10:01:00Z",
            "source_id": "mars/telemetry/solar_array/Panel_A",
            "source_type": "telemetry",
            "status": "ok",
            "metrics": [
                {"name": "power", "value": 15.5, "unit": "kw"},
                {"name": "voltage", "value": 120.0, "unit": "v"},
                {"name": "current", "value": 129.1, "unit": "a"}
            ]
        }
        ```

# Actuator Command Schema

format to send to actuators

```json
{
    "actuator_id": "string",
    "action": "string",
    "reason": "string"
}
```

- Examples

    1.
        ```json
        {
            "actuator_id": "ventilation_fan",
            "action": "ON",
            "reason": "pm25_exceeded_threshold"
        }
        ```
