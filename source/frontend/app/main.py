# frontend/app.py
import os
import json
import time
import pika
from flask import Flask, render_template, request, jsonify # <-- Aggiunto jsonify
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

    # Aggiunto il callback per quando regola triggerata
    def callback(ch, method, properties, body):
        try:
            data = json.loads(body.decode('utf-8'))
            
            # NUOVO: Smistiamo il messaggio in base al tipo
            if data.get("type") == "actuator_update":
                socketio.emit('actuator_update', data)
            elif data.get("type") == "rule_triggered":
                socketio.emit('rule_triggered', data)
            else:
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

# ==========================================
# ROTTE PROXY VERSO IL PROCESSING ENGINE
# ==========================================
ENGINE_URL = "http://processing-engine:8001"

@app.route("/rules", methods=["GET", "POST"])
def manage_rules():
    if request.method == "POST":
        # Ora il browser invia un JSON tramite Javascript, non più un Form HTML!
        rule_data = request.json
        
        # Inoltriamo il JSON al Processing Engine
        try:
            response = requests.post(f"{ENGINE_URL}/rules", json=rule_data, timeout=5)
            # Rispondiamo al Javascript dicendo che è andato tutto bene
            return jsonify({"status": "success"}), 200
        except Exception as e:
            print(f"Errore di invio regola: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
            
    # Se è una GET, recuperiamo la lista aggiornata
    rules_list = []
    try:
        response = requests.get(f"{ENGINE_URL}/rules", timeout=5)
        if response.status_code == 200:
            rules_list = response.json()
    except Exception as e:
        print(f"Errore nel recupero regole: {e}")

    return render_template("rules.html", existing_rules=rules_list)


@app.route("/rules/<int:rule_id>", methods=["DELETE"])
def delete_rule(rule_id):
    """Proxy per eliminare una regola"""
    try:
        response = requests.delete(f"{ENGINE_URL}/rules/{rule_id}", timeout=5)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        print(f"Errore delete regola: {e}")
        return jsonify({"status": "error"}), 500

@app.route("/rules/update", methods=['POST'])
def update_rule():
    rule_data = request.json

    try:
        response = requests.post(f"{ENGINE_URL}/rules/update", json=rule_data, timeout=5)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Errore di invio regola: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/rules/<int:rule_id>/toggle", methods=["POST"])
def toggle_rule(rule_id):
    """Proxy per attivare/disattivare una regola"""
    try:
        # Recuperiamo il JSON inviato dal Javascript { "enabled": true/false }
        payload = request.json 
        response = requests.post(f"{ENGINE_URL}/rules/{rule_id}/toggle", json=payload, timeout=5)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        print(f"Errore toggle regola: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/history')
def history():
    return render_template("history.html")

@app.route('/api/history', methods=['GET'])
def get_history_api():
    try:
        response = requests.get(f"{ENGINE_URL}/history", timeout=5)
        return jsonify(response.json()), 200
    except:
        return jsonify([]), 500
# ==========================================

@app.route("/sensors-actuators")
def sensors_actuators():
    sensors_list = []
    actuators_list = []
    descriptions_map = {
        # Sensori Ambientali e Moduli
        "corridor_pressure": "Pressione atmosferica nei condotti di collegamento tra i moduli.",
        "air_quality_voc": "Concentrazione di composti organici volatili nell'aria abitabile.",
        "air_quality_pm25": "Monitoraggio polveri sottili e particolato in sospensione.",
        "entrance_humidity": "Livello di umidità relativa rilevato nel modulo d'ingresso.",
        "co2_hall": "Concentrazione di anidride carbonica nel corridoio principale.",
        "water_tank_level": "Livello di riempimento dei serbatoi idrici centrali.",
        "test": "Canale di test per la verifica dei protocolli di comunicazione.",
        
        # Coltivazioni e Biosfera
        "hydroponic_ph": "Acidità della soluzione nutritiva nel sistema idroponico.",
        "greenhouse_temperature": "Temperatura ambiente all'interno della serra botanica.",
        
        # Stream di Telemetria Avanzata (MQTT/Telemetry)
        "mars/telemetry/life_support": "Stato operativo del sistema primario di supporto vitale.",
        "mars/telemetry/thermal_loop": "Monitoraggio del fluido termovettore per il riscaldamento base.",
        "mars/telemetry/solar_array": "Efficienza e output energetico dei pannelli fotovoltaici.",
        "mars/telemetry/airlock": "Integrità strutturale e stato della camera di compensazione.",
        "mars/telemetry/power_consumption": "Assorbimento energetico totale istantaneo della base.",
        "mars/telemetry/radiation": "Rilevamento radiazioni ionizzanti e attività solare esterna.",
        "mars/telemetry/power_bus": "Distribuzione del carico elettrico sulla rete principale.",
    }
    try:
        resp_s = requests.get(f"{ENGINE_URL}/sensors", timeout=2)
        if resp_s.status_code == 200:
            sensors_list = resp_s.json()
        
        resp_a = requests.get(f"{ENGINE_URL}/actuators", timeout=2)
        if resp_a.status_code == 200:
            actuators_list = resp_a.json()
    except Exception as e:
        print(f"Errore connessione engine: {e}")

    return render_template("sensors_actuators.html", sensors=sensors_list, actuators=actuators_list, descriptions=descriptions_map)

@app.route("/actuators/<actuator_id>/toggle", methods=["POST"])
def proxy_actuator_toggle(actuator_id):
    try:
        payload = request.json 
        response = requests.post(f"{ENGINE_URL}/actuators/{actuator_id}/toggle", json=payload, timeout=5)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"status": "error"}), 500


@app.route("/api/latest-telemetry")
def proxy_latest_telemetry():
    """Proxy per recuperare i dati in cache dal Processing Engine"""
    try:
        response = requests.get(f"{ENGINE_URL}/telemetry/latest", timeout=2)
        if response.status_code == 200:
            return jsonify(response.json())
        return jsonify({})
    except Exception as e:
        print(f"Errore nel recupero della cache telemetria: {e}")
        return jsonify({})


if __name__ == "__main__":
    socketio.start_background_task(rabbitmq_consumer)
    
    socketio.run(app, host="0.0.0.0", port=8000, allow_unsafe_werkzeug=True)