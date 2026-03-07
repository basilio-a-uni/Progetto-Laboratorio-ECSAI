import messaging
import asyncio
import websockets
import aiohttp
import json

TOPICS = [
    T_SOLAR_ARRAY := "mars/telemetry/solar_array",
    T_RADIATION := "mars/telemetry/radiation",
    T_LIFE_SUPPORT := "mars/telemetry/life_support",
    T_THERMAL_LOOP := "mars/telemetry/thermal_loop",
    T_POWER_BUS := "mars/telemetry/power_bus",
    T_POWER_CONSUMPTION := "mars/telemetry/power_consumption",
    T_AIRLOCK := "mars/telemetry/airlock"
]

TOPIC_POWER_V1 = (T_SOLAR_ARRAY, T_POWER_BUS, T_POWER_CONSUMPTION)
TOPIC_ENVIRONMENT_V1 = (T_RADIATION, T_LIFE_SUPPORT)
TOPIC_THERMAL_LOOP_V1 = (T_THERMAL_LOOP,)
TOPIC_AIRLOCK_V1 = (T_AIRLOCK,)


REST_SENSORS = [
    S_GREENHOUSE_TEMPERATURE := "greenhouse_temperature",
    S_ENTRANCE_HUMIDITY := "entrance_humidity",
    S_CO2_HALL := "co2_hall",
    S_HYDROPONIC_PH := "hydroponic_ph",
    S_WATER_TANK_LEVEL := "water_tank_level",
    S_CORRIDOR_PRESSURE := "corridor_pressure",
    S_AIR_QUALITY_PM25 := "air_quality_pm25",
    S_AIR_QUALITY_VOC := "air_quality_voc"
]

REST_SCALAR_V1 = (S_GREENHOUSE_TEMPERATURE, S_ENTRANCE_HUMIDITY, S_CO2_HALL, S_CORRIDOR_PRESSURE)
REST_CHEMISTRY_V1 = (S_HYDROPONIC_PH, S_AIR_QUALITY_VOC)
REST_PARTICULATE_V1 = (S_AIR_QUALITY_PM25,)
REST_LEVEL_V1 = (S_WATER_TANK_LEVEL,)


def unify_topic(topic: str, data: dict) -> dict:
    if topic is None:
        raise NotImplementedError("Il topic non può essere None")
        
    new_data = dict()
    
    # Campi comuni a tutti i topic
    new_data["timestamp"] = data["event_time"]
    new_data["source_id"] = topic
    new_data["source_type"] = "telemetry"

    # Regole specifiche per power.v1
    if topic in TOPIC_POWER_V1:
        new_data["status"] = "ok"
        new_data["metrics"] = [
            {"name": "power_kw", "value": data["power_kw"], "unit": "kW"},
            {"name": "voltage_v", "value": data["voltage_v"], "unit": "V"},
            {"name": "current_a", "value": data["current_a"], "unit": "A"},
            {"name": "cumulative_kwh", "value": data["cumulative_kwh"], "unit": "kWh"}
        ]

    # Regole specifiche per environment.v1
    elif topic in TOPIC_ENVIRONMENT_V1:
        new_data["status"] = data["status"]
        new_data["metrics"] = [
            {"name": m["metric"], "value": m["value"], "unit": m["unit"]} 
            for m in data.get("measurements", [])
        ]

    # Regole specifiche per thermal_loop.v1
    elif topic in TOPIC_THERMAL_LOOP_V1:
        new_data["status"] = data["status"]
        new_data["metrics"] = [
            {"name": "temperature_c", "value": data["temperature_c"], "unit": "C"},
            {"name": "flow_l_min", "value": data["flow_l_min"], "unit": "L/min"}
        ]

    # Regole specifiche per airlock.v1
    elif topic in TOPIC_AIRLOCK_V1:
        new_data["status"] = "ok"
        new_data["metrics"] = [
            {"name": "cycles_per_hour", "value": data["cycles_per_hour"], "unit": "cycles/hour"}
        ]

    else:
        raise NotImplementedError(f"Normalizzazione non implementata per il topic: {topic}")

    return new_data



def unify_sensor(sensor_id: str, data: dict) -> dict:
    if sensor_id is None:
        raise ValueError("Il sensor_id non può essere None")
        
    new_data = dict()
    
    # Campi comuni a tutti i sensori REST
    new_data["timestamp"] = data["captured_at"]
    new_data["source_id"] = sensor_id
    new_data["source_type"] = "rest"
    new_data["status"] = data["status"]

    # Mapping esplicito verso rest.scalar.v1
    if sensor_id in REST_SCALAR_V1:
        new_data["metrics"] = [
            {"name": data["metric"], "value": data["value"], "unit": data["unit"]}
        ]
        
    # Mapping esplicito verso rest.chemistry.v1
    elif sensor_id in REST_CHEMISTRY_V1:
        new_data["metrics"] = [
            {"name": m["metric"], "value": m["value"], "unit": m["unit"]} 
            for m in data.get("measurements", [])
        ]
        
    # Mapping esplicito verso rest.particulate.v1
    elif sensor_id in REST_PARTICULATE_V1:
        new_data["metrics"] = [
            {"name": "pm1", "value": data["pm1_ug_m3"], "unit": "ug/m3"},
            {"name": "pm2.5", "value": data["pm25_ug_m3"], "unit": "ug/m3"},
            {"name": "pm10", "value": data["pm10_ug_m3"], "unit": "ug/m3"}
        ]
        
    # Mapping esplicito verso rest.level.v1
    elif sensor_id in REST_LEVEL_V1:
        new_data["metrics"] = [
            {"name": "level_pct", "value": data["level_pct"], "unit": "percent"},
            {"name": "level_liters", "value": data["level_liters"], "unit": "L"}
        ]
        
    else:
        raise NotImplementedError(f"Schema non riconosciuto o mappatura mancante per il sensore: {sensor_id}")

    return new_data







async def consume_topic(topic):
    uri = f"ws://simulator:8080/api/telemetry/ws?topic={topic}"
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                print(f"[*] Sottoscritto al topic: {topic}")
                while True:
                    message = await websocket.recv()
                    data = json.loads(message)
                    
                    # unify the data
                    data = unify_topic(topic, data)
                    # send the data
                    messaging.send_message(data)

                    print("Stream telemetry:")
                    print(f"[{topic}] Dati: {data}")
        except Exception as e:
            print(f"[!] Errore su {topic}: {e}. Riprovo tra 5s...")
            await asyncio.sleep(5)


async def poll_rest(sensor):
    uri = f"http://simulator:8080/api/sensors/{sensor}"
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get(uri) as response:
                    data = await response.json()
                    
                    # unify the data
                    data = unify_sensor(sensor, data)
                    # send the data
                    messaging.send_message(data)

                    print("Rest sensor:")
                    print(f"[{sensor}] Dati: {data}")

            except Exception as e:
                print(f"[!] REST error on {sensor}: {e}")
            await asyncio.sleep(5)



async def main():
    await asyncio.gather(
            *(consume_topic(t) for t in TOPICS),
            *(poll_rest(s) for s in REST_SENSORS)
        )

if __name__ == "__main__":
    data_example = {
        "source_id": "test",
        "timestamp": "2026-03-06T11:45:00",
        "rest_sensors": {"greenhouse_temp": 22.5, "co2_hall": 450},
        "telemetry": {"topic_alpha": 10.2}
    }

    messaging.send_message(data_example)

    asyncio.run(main())