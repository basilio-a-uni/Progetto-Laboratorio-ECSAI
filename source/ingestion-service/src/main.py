# import messaging
# import websocket
# import json
# import threading
# import time
# import requests


# def on_message(ws, message):
#     """Questa funzione scatta automaticamente quando arriva un dato dal WebSocket"""
#     raw_data = json.loads(message)
#     print(f"[STREAM] Nuovo dato ricevuto: {raw_data}")
    
#     # -> QUI trasformerai raw_data nel tuo Unified Schema
#     # -> QUI invierai il dato a RabbitMQ

# def on_error(ws, error):
#     print(f"Errore WebSocket: {error}")

# def on_close(ws, close_status_code, close_msg):
#     print("Connessione WebSocket chiusa.")

# def start_ws_stream(topic):
#     """Apre una connessione WebSocket per un topic specifico"""
#     # L'URL esatto fornito dalle tue specifiche
#     ws_url = f"ws://simulator:8080/api/telemetry/ws?topic={topic}"
    
#     ws = websocket.WebSocketApp(
#         ws_url,
#         on_message=on_message,
#         on_error=on_error,
#         on_close=on_close
#     )
#     # Avvia l'ascolto infinito
#     ws.run_forever()




# if __name__ == "__main__":
#     data_example = {
#         "timestamp": "2026-03-06T11:45:00",
#         "rest_sensors": {"greenhouse_temp": 22.5, "co2_hall": 450},
#         "telemetry": {"topic_alpha": 10.2}
#     }

#     messaging.send_message(data_example)


# if __name__ == "__main__":
#     print("Inizializzazione Ingestion Service su Marte...")
    
#     # 1. Avvia il thread per il polling dei sensori REST
#     rest_thread = threading.Thread(target=poll_rest_sensors)
#     rest_thread.daemon = True
#     rest_thread.start()
    
#     # 2. Scopri i topic di telemetria e avvia un WebSocket per ciascuno
#     try:
#         # Usa l'endpoint indicato nelle tue docs per scoprire i topic
#         topics_response = requests.get("http://simulator:8080/api/telemetry/topics")
#         topics_list = topics_response.json()
        
#         for topic in topics_list:
#             # Crea un thread separato per ascoltare ogni singolo topic
#             ws_thread = threading.Thread(target=start_ws_stream, args=(topic,))
#             ws_thread.daemon = True
#             ws_thread.start()
#             print(f"Avviato ascolto stream per {topic}")
            
#     except Exception as e:
#         print(f"Impossibile recuperare i topic di telemetria: {e}")

#     # Mantieni il container attivo
#     while True:
#         time.sleep(1)





# SSECLIENT ---------------------------


# import requests
# import json
# from sseclient import SSEClient


# def test_stream():
#     # IL TRUCCO È QUI: usiamo host.docker.internal invece di localhost
#     url = "http://host.docker.internal:8080/api/telemetry/stream/mars/telemetry/solar_array"
    
#     print(f"📡 Tentativo di connessione a {url}...")
    
#     try:
#         # stream=True mantiene la connessione aperta
#         response = requests.get(url, stream=True)
#         response.raise_for_status() # Lancia un errore se lo status non è 200 OK
        
#         client = SSEClient(response)
#         print("✅ Connessione stabilita! In attesa della telemetria...")
        
#         # Ciclo infinito che stampa i dati man mano che arrivano
#         for event in client.events():
#             if event.data:
#                 data = json.loads(event.data)
#                 print(f"🪐 Dati da Marte: {data}")
                
#     except Exception as e:
#         print(f"❌ Errore: {e}")
#         print("💡 Se 'host.docker.internal' fallisce, metti al suo posto l'IP LAN del tuo PC (es. 192.168.1.X).")

# if __name__ == "__main__":
#     test_stream()








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
            poll_rest("greenhouse_temperature")
            #*(consume_topic(t) for t in TOPICS),
            #*(poll_rest(s) for s in REST_SENSORS)
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