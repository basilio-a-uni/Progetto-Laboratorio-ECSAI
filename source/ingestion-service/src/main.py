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
TOPIC_THERMAL_LOOP_V1 = (T_THERMAL_LOOP)
TOPIC_AIRLOCK_V1 = (T_AIRLOCK)


REST_SENSORS = [
    "greenhouse_temperature",
    "entrance_humidity",
    "co2_hall",
    "hydroponic_ph",
    "water_tank_level",
    "corridor_pressure"
    "air_quality_pm25",
    "air_quality_voc"
]

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
                    # send the data

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
                    # send the data

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
        "timestamp": "2026-03-06T11:45:00",
        "rest_sensors": {"greenhouse_temp": 22.5, "co2_hall": 450},
        "telemetry": {"topic_alpha": 10.2}
    }

    messaging.send_message(data_example)

    asyncio.run(main())