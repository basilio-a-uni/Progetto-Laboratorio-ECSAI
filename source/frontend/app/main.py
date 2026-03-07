# frontend/app.py
import os
import json
import time
import pika
from flask import Flask, render_template, request
from flask_socketio import SocketIO
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mars-secret-key'  # for flask websocket

# Inizializziamo SocketIO in modalità threading nativa
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

RABBIT_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
EXCHANGE_NAME = 'mars_telemetry_exchange'

def get_rabbit_connection():
    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST))
            return connection
        except pika.exceptions.AMQPConnectionError:
            print("[!] RabbitMQ non disponibile per il frontend, riprovo tra 2s...")
            time.sleep(2)

def rabbitmq_consumer():
    """Gira in background e ascolta il Fanout Exchange"""
    connection = get_rabbit_connection()
    channel = connection.channel()

    # Ci assicuriamo che l'exchange esista
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='fanout')

    # Creiamo una coda esclusiva e temporanea solo per questo frontend
    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue

    # Leghiamo la nostra coda privata al megafono (Exchange)
    channel.queue_bind(exchange=EXCHANGE_NAME, queue=queue_name)

    def callback(ch, method, properties, body):
        try:
            # Decodifichiamo l'Unified Schema dal JSON
            data = json.loads(body.decode('utf-8'))
            # Lo spariamo al browser connesso via WebSocket
            socketio.emit('telemetry_update', data)
        except Exception as e:
            print(f"Errore nel parsing del messaggio: {e}")

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    
    print("[*] Frontend in ascolto sulla telemetria live...")
    channel.start_consuming()

@app.route("/")
def home():
    # Renderizza la nostra dashboard
    return render_template("index.html")



ENGINE_URL = "http://processing-engine:8001"

# @app.route("/rules", methods=["GET", "POST"])
# def manage_rules():
#     if request.method == "POST":
#         # Estraiamo i dati dal form HTML
#         rule_data = {
#             "sensor_name": request.form.get("sensor_name"),
#             "metric": request.form.get("metric"),
#             "operator": request.form.get("operator"),
#             "sensor_target_value": request.form.get("sensor_target_value"),
#             "actuator_name": request.form.get("actuator_name"),
#             "actuator_set_value": request.form.get("actuator_set_value")
#         }
        
#         # Inoltriamo il comando al Processing Engine via API REST
#         try:
#             requests.post(f"{ENGINE_URL}/rules", json=rule_data, timeout=5)
#         except Exception as e:
#             print(f"Errore di comunicazione col Processing Engine: {e}")
            
#     # Se è una GET, o dopo aver inviato la POST, mostriamo la pagina
#     return render_template("rules.html")

@app.route("/rules", methods=["GET", "POST"])
def manage_rules():
    if request.method == "POST":
        # 1. Estraiamo i dati dal form HTML
        rule_data = {
            "sensor_name": request.form.get("sensor_name"),
            "metric": request.form.get("metric"),
            "operator": request.form.get("operator"),
            "sensor_target_value": request.form.get("sensor_target_value"),
            "actuator_name": request.form.get("actuator_name"),
            "actuator_set_value": request.form.get("actuator_set_value")
        }
        
        # 2. Inviamo la nuova regola al motore
        try:
            requests.post(f"{ENGINE_URL}/rules", json=rule_data, timeout=5)
        except Exception as e:
            print(f"Errore di invio regola: {e}")
            
    # --- NOVITÀ: RECUPERIAMO LA LISTA AGGIORNATA ---
    rules_list = []
    try:
        # Facciamo una GET al Processing Engine per avere tutte le regole
        response = requests.get(f"{ENGINE_URL}/rules", timeout=5)
        if response.status_code == 200:
            rules_list = response.json()
    except Exception as e:
        print(f"Errore nel recupero regole: {e}")

    # 3. Passiamo existing_rules al template
    return render_template("rules.html", existing_rules=rules_list)



@app.route("/sensors-actuators")
def sensors_actuators():
    # Per ora renderizziamo solo la pagina statica. 
    # In futuro potresti voler fare una GET al tuo motore per caricare lo stato iniziale degli attuatori
    return render_template("sensors_actuators.html")



if __name__ == "__main__":
    # Avviamo il consumer RabbitMQ in un thread in background
    socketio.start_background_task(rabbitmq_consumer)
    
    # Avviamo il server Flask con supporto WebSocket
    socketio.run(app, host="0.0.0.0", port=8000, allow_unsafe_werkzeug=True)