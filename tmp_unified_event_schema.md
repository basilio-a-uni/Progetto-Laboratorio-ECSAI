# Contents
- **Unified Event Schema** (input data from sensors/telemetry)
- **Actuator Command Schema** (output data to actuators)

# Unified Event Schema

All incoming payloads from REST sensors and telemetry streams are converted into a unified internal event schema to ensure consistent processing across the system.

Each payload generates one normalized event. The timestamp is derived from the original message, the source identifier corresponds to the sensor or topic name, and the source type indicates whether the data comes from REST polling or telemetry streaming. 

All numeric observations are mapped into the metrics array. This approach allows the rule engine, state cache, and dashboard to operate on a consistent data format regardless of the original device schema.


```json
{
  "timestamp": "2036-03-06T10:42:10Z",
  "source_id": "string",
  "source_type": "rest | telemetry",
  "status": "ok | warning",
  "metrics": [
    {
      "name": "string",
      "value": 0.0,
      "unit": "string"
    }
  ]
}
```
## Normalization Rules

### Rest Sensors

#### - `rest.scalar.v1`

- `timestamp` ← `captured_at`
- `source_id` ← `sensor_id`
- `source_type` ← `"rest"`
- `status` ← `status`
- `metrics` contains one entry:
    - `name` ← `metric`
    - `value` ← `value`
    - `unit` ← `unit`

- Example:

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

#### - `rest.chemistry.v1`

- `timestamp` ← `captured_at`
- `source_id` ← `sensor_id`
- `source_type` ← `"rest"`
- `status` ← `status`
- `metrics` contains one entry for each element in `measurements`:
    - `name` ← `metric`
    - `value` ← `value`
    - `unit` ← `unit`

- Example:

```json
{
    "sensor_id": "hydroponic_ph",
    "captured_at": "2036-03-06T10:42:10Z",
    "measurements": [
        { "metric": "ph", "value": 6.2, "unit": "pH" },
        { "metric": "conductivity", "value": 1.8, "unit": "mS/cm" }
    ],
    "status": "ok"
}
```
→
```json
{
    "timestamp": "2036-03-06T10:42:10Z",
    "source_id": "hydroponic_ph",
    "source_type": "rest",
    "status": "ok",
    "metrics": [
        {"name": "ph", "value": 6.2, "unit": "pH"},
        {"name": "conductivity", "value": 1.8, "unit": "mS/cm"}
    ]
}
```

#### - `rest.particulate.v1`

- `timestamp` ← `captured_at`
- `source_id` ← `sensor_id`
- `source_type` ← `"rest"`
- `status` ← `status`
- `metrics` contains three entries:
    - `name` ← `"pm1"`
    - `value` ← `pm1_ug_m3`
    - `unit` ← `"ug/m3"`

    - `name` ← `"pm2.5"`
    - `value` ← `pm25_ug_m3`
    - `unit` ← `"ug/m3"`

    - `name` ← `"pm10"`
    - `value` ← `pm10_ug_m3`
    - `unit` ← `"ug/m3"`

- Example:

```json
{
    "sensor_id": "air_quality_pm25",
    "captured_at": "2036-03-06T10:42:10Z",
    "pm1_ug_m3": 12.4,
    "pm25_ug_m3": 18.7,
    "pm10_ug_m3": 25.3,
    "status": "ok"
}
```
→
```json
{
    "timestamp": "2036-03-06T10:42:10Z",
    "source_id": "air_quality_pm25",
    "source_type": "rest",
    "status": "ok",
    "metrics": [
        {"name": "pm1", "value": 12.4, "unit": "ug/m3"},
        {"name": "pm2.5", "value": 18.7, "unit": "ug/m3"},
        {"name": "pm10", "value": 25.3, "unit": "ug/m3"}
    ]
}
```


#### - `rest.level.v1`

- `timestamp` ← `captured_at`
- `source_id` ← `sensor_id`
- `source_type` ← `"rest"`
- `status` ← `status`
- `metrics` contains two entries:
    - `name` ← `"level_pct"`
    - `value` ← `level_pct`
    - `unit` ← `"percent"`

    - `name` ← `"level_liters"`
    - `value` ← `level_liters`
    - `unit` ← `"L"`

- Example:

```json
{
    "sensor_id": "water_tank_level",
    "captured_at": "2036-03-06T10:42:10Z",
    "level_pct": 72.5,
    "level_liters": 145.0,
    "status": "ok"
}
```
→
```json
{
    "timestamp": "2036-03-06T10:42:10Z",
    "source_id": "water_tank_level",
    "source_type": "rest",
    "status": "ok",
    "metrics": [
        {"name": "level_pct", "value": 72.5, "unit": "percent"},
        {"name": "level_liters", "value": 145.0, "unit": "L"}
    ]
}
```
### Telemetry Topics

#### - `topic.power.v1`

- `timestamp` ← `event_time`
- `source_id` ← `topic`
- `source_type` ← `"telemetry"`
- `status` ← `"ok"`
- `metrics` contains four entries:
    - `name` ← `"power_kw"`
    - `value` ← `power_kw`
    - `unit` ← `"kW"`

    - `name` ← `"voltage_v"`
    - `value` ← `voltage_v`
    - `unit` ← `"V"`

    - `name` ← `"current_a"`
    - `value` ← `current_a`
    - `unit` ← `"A"`

    - `name` ← `"cumulative_kwh"`
    - `value` ← `cumulative_kwh`
    - `unit` ← `"kWh"`

- Example:

```json
{
    "topic": "mars/telemetry/solar_array",
    "event_time": "2036-03-06T10:42:10Z",
    "subsystem": "solar_array",
    "power_kw": 4.6,
    "voltage_v": 120.5,
    "current_a": 38.2,
    "cumulative_kwh": 15432.7
}
```
→
```json
{
    "timestamp": "2036-03-06T10:42:10Z",
    "source_id": "mars/telemetry/solar_array",
    "source_type": "telemetry",
    "status": "ok",
    "metrics": [
        {"name": "power_kw", "value": 4.6, "unit": "kW"},
        {"name": "voltage_v", "value": 120.5, "unit": "V"},
        {"name": "current_a", "value": 38.2, "unit": "A"},
        {"name": "cumulative_kwh", "value": 15432.7, "unit": "kWh"}
    ]
}
```

#### - `topic.environment.v1`

- `timestamp` ← `event_time`
- `source_id` ← `topic`
- `source_type` ← `"telemetry"`
- `status` ← `status`
- `metrics` contains one entry for each element in `measurements`:
    - `name` ← `metric`
    - `value` ← `value`
    - `unit` ← `unit`

- Example:

```json
{
    "topic": "mars/telemetry/life_support",
    "event_time": "2036-03-06T10:42:10Z",
    "source": {
        "system": "life_support",
        "segment": "habitat_A"
    },
    "measurements": [
        {"metric": "oxygen_pct", "value": 20.8, "unit": "%"},
        {"metric": "co2_ppm", "value": 650, "unit": "ppm"}
    ],
    "status": "ok"
}
```
→
```json
{
    "timestamp": "2036-03-06T10:42:10Z",
    "source_id": "mars/telemetry/life_support",
    "source_type": "telemetry",
    "status": "ok",
    "metrics": [
        {"name": "oxygen_pct", "value": 20.8, "unit": "%"},
        {"name": "co2_ppm", "value": 650, "unit": "ppm"}
    ]
}
```

#### - `topic.thermal_loop.v1`

- `timestamp` ← `event_time`
- `source_id` ← `topic`
- `source_type` ← `"telemetry"`
- `status` ← `status`
- `metrics` contains two entries:
    - `name` ← `"temperature_c"`
    - `value` ← `temperature_c`
    - `unit` ← `"C"`

    - `name` ← `"flow_l_min"`
    - `value` ← `flow_l_min`
    - `unit` ← `"L/min"`

- Example:

```json
{
    "topic": "mars/telemetry/thermal_loop",
    "event_time": "2036-03-06T10:42:10Z",
    "loop": "coolant_loop_A",
    "temperature_c": 18.6,
    "flow_l_min": 12.4,
    "status": "ok"
}
```
→
```json
{
    "timestamp": "2036-03-06T10:42:10Z",
    "source_id": "mars/telemetry/thermal_loop",
    "source_type": "telemetry",
    "status": "ok",
    "metrics": [
        {"name": "temperature_c", "value": 18.6, "unit": "C"},
        {"name": "flow_l_min", "value": 12.4, "unit": "L/min"}
    ]
}
```

#### `topic.airlock.v1`

- `timestamp` ← `event_time`
- `source_id` ← `topic`
- `source_type` ← `"telemetry"`
- `status` ← `"ok"`
- `metrics` contains one entry:
    - `name` ← `"cycles_per_hour"`
    - `value` ← `cycles_per_hour`
    - `unit` ← `"cycles/hour"`

- Example:

```json
{
    "topic": "mars/telemetry/airlock",
    "event_time": "2036-03-06T10:42:10Z",
    "airlock_id": "airlock_A",
    "cycles_per_hour": 3.2,
    "last_state": "IDLE"
}
```
→
```json
{
    "timestamp": "2036-03-06T10:42:10Z",
    "source_id": "mars/telemetry/airlock",
    "source_type": "telemetry",
    "status": "ok",
    "metrics": [
        {"name": "cycles_per_hour", "value": 3.2, "unit": "cycles/hour"}
    ]
}
```

# Actuator Command Schema

Internal format used by the rule engine before calling the actuator API.

```json
{
    "actuator_id": "string",  
    "state": "ON | OFF",      
    "reason": "string"        
}
```


- Example:
    ```json
    {
        "actuator_id": "ventilation_fan", 
        "state": "ON", 
        "reason": "pm25_exceeded_threshold"
    }
    ```
