import pika
import json
import os
import time
import threading
from datetime import datetime, timezone
from flask import Flask, request, jsonify 

import database

from entities import State, Rule

app = Flask(__name__)

def get_connection():
    rabbit_host = os.getenv('RABBITMQ_HOST', 'localhost')
    while True:
        try:
            print("Testing connection")
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=rabbit_host)
            )
            print("Successful connection")
            return connection
        except:
            print(" [!] RabbitMQ not yet started. Retry in 5 seconds.")
            time.sleep(5)


def inject_callback(state):
    def callback(ch, method, properties, body):
        data = json.loads(body)
        # print(f"Ricevuto dati : {data}\n")

        state.update(data)
        

        ch.basic_ack(delivery_tag=method.delivery_tag)
    return callback

def start_consuming(state):
    connection = get_connection()
    channel = connection.channel()

    channel.exchange_declare(exchange='mars_telemetry_exchange', exchange_type='fanout')
    
    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue
    
    channel.queue_bind(exchange='mars_telemetry_exchange', queue=queue_name)

    channel.basic_consume(
        queue=queue_name, 
        on_message_callback=inject_callback(state), 
        auto_ack=False
    )
    
    print("[*] Processing Engine in ascolto su RabbitMQ")
    channel.start_consuming()

# NUOVO: Funzione per pubblicare aggiornamenti su RabbitMQ
def publish_actuator_update(actuator_id, new_state):
    try:
        connection = get_connection()
        channel = connection.channel()
        channel.exchange_declare(exchange='mars_telemetry_exchange', exchange_type='fanout')
        
        message = {
            "type": "actuator_update",
            "actuator_id": actuator_id,
            "state": new_state
        }
        channel.basic_publish(exchange='mars_telemetry_exchange', routing_key='', body=json.dumps(message))
        connection.close()
    except Exception as e:
        print(f"Errore pubblicazione aggiornamento attuatore: {e}")

def publish_rule_triggered(rule, actual_value):
    try:
        connection = get_connection()
        channel = connection.channel()
        channel.exchange_declare(exchange='mars_telemetry_exchange', exchange_type='fanout')

        message = {
            "type": "rule_triggered",
            "rule_id": rule.id,
            "sensor_name": rule.sensor_name,
            "metric": rule.metric,
            "operator": rule.operator,
            "sensor_target_value": rule.sensor_target_value,
            "actual_value": actual_value,
            "actuator_name": rule.actuator_name,
            "actuator_set_value": rule.actuator_set_value,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        channel.basic_publish(
            exchange='mars_telemetry_exchange',
            routing_key='',
            body=json.dumps(message)
        )
        connection.close()
    except Exception as e:
        print(f"Errore pubblicazione evento rule_triggered: {e}")


# --- ROTTE PER IL FRONTEND ---

@app.route('/rules', methods=['GET', 'POST'])
def handle_rules():
    if request.method == 'POST':
        data = request.json
        # Passiamo i dati direttamente al metodo, l'ID lo gestirà il database
        state.create_new_rule({
            'sensor_name': data['sensor_name'],
            'metric': data['metric'],
            'operator': data['operator'],
            'sensor_target_value': float(data['sensor_target_value']),
            'actuator_name': data['actuator_name'],
            'actuator_set_value': data['actuator_set_value']
        })
        return jsonify({"status": "success"}), 201
    
    else:
        # GET: Mandiamo al frontend la lista di tutte le regole inclusi ID e stato
        all_rules = []
        for sensor in state.current_rules:
            for r in state.current_rules[sensor]:
                all_rules.append({
                    "id": r.id,  
                    "sensor_name": r.sensor_name,
                    "metric": r.metric,
                    "operator": r.operator,
                    "sensor_target_value": r.sensor_target_value,
                    "actuator_name": r.actuator_name,
                    "actuator_set_value": r.actuator_set_value,
                    "enabled": r.enabled
                })
        return jsonify(all_rules)

# NUOVO: Elimina regola
@app.route('/rules/<int:rule_id>', methods=['DELETE'])
def delete_rule(rule_id):
    try:
        state.delete_rule(rule_id) 
        return jsonify({"status": "success", "message": f"Rule {rule_id} deleted"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/rules/update', methods=['POST'])
def update_rule():
    data = request.json
    try:
        state.update_rule(data)
        del state.triggered_rules_history[int(data["id"])]
        return jsonify({"status": "success", "message": f"Rule {data['id']} updated"}), 200
    except Exception as e:
        print("Update error:", str(e))

        return jsonify({"status": "error", "message": str(e)}), 500

# NUOVO: Attiva/Disattiva regola
@app.route('/rules/<int:rule_id>/toggle', methods=['POST'])
def toggle_rule(rule_id):
    data = request.json
    is_enabled = data.get('enabled')
    try:
        state.toggle_rule(rule_id, is_enabled)
        return jsonify({"status": "success", "message": f"Rule {rule_id} status changed to {is_enabled}"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/history', methods=['GET'])
def history():
    result = []
    for sensor in state.current_rules:
        for r in state.current_rules[sensor]:
            if r.id in state.triggered_rules_history:
                result.append({
                    "id": r.id,  
                    "sensor_name": r.sensor_name,
                    "metric": r.metric,
                    "operator": r.operator,
                    "sensor_target_value": r.sensor_target_value,
                    "triggered_at": state.triggered_rules_history[r.id]["triggered_at"],
                    "last_trigger_value": state.triggered_rules_history[r.id]["last_trigger_value"]
                })
    return jsonify(result)
    

# --- NUOVI ENDPOINT PER SENSORI E ATTUATORI ---

@app.route('/sensors', methods=['GET'])
def get_sensors():
    sensors = []
    # Usiamo i sensori che hanno inviato dati o quelli presenti nelle regole
    source_ids = set(state.sensor_data.keys()) | set(state.current_rules.keys())
    
    for s_id in source_ids:
        print(sensors)
        print(s_id)
        if s_id.startswith('mars/telemetry/'):
            source_type = 'telemetry'
        else:
            source_type = 'rest'
            
        latest_data = state.sensor_data.get(s_id, {})
        current_status = latest_data.get('status', 'OK') # Se è nuovo, diciamo 'OK' di default
        
        sensors.append({
            "source_id": s_id,
            "source_type": source_type,
            "status": current_status
        })
        
    return jsonify(sensors)


@app.route('/actuators', methods=['GET'])
def get_actuators():
    # Trasformiamo il dizionario current_actuators_status in una lista per il frontend
    actuators = []
    for name, status in state.current_actuators_status.items():
        actuators.append({
            "id": name,
            "name": name.replace("_", " ").title(), # 'cooling_fan' -> 'Cooling Fan'
            "state": status
        })
    return jsonify(actuators)

@app.route('/actuators/<actuator_id>/toggle', methods=['POST'])
def toggle_actuator(actuator_id):
    data = request.json
    new_state = data.get('state') # "ON" o "OFF"
    if actuator_id in state.current_actuators_status:
        state.current_actuators_status[actuator_id] = new_state
        print(f"[Manual Control] Actuator {actuator_id} set to {new_state}")
        
        # NUOVO: Avvisiamo il frontend (e chiunque altro ascolti) che l'attuatore è cambiato
        publish_actuator_update(actuator_id, new_state)
        
        return jsonify({"status": "success"}), 200
    return jsonify({"status": "error", "message": "Actuator not found"}), 404


@app.route('/telemetry/latest', methods=['GET'])
def get_latest_telemetry():
    """Restituisce tutta la cache degli ultimi messaggi ricevuti"""
    return jsonify(state.sensor_data)

if __name__ == "__main__":
    database.init_db()
    global state

    state = State(
    on_actuator_change=publish_actuator_update,
    on_rule_triggered=publish_rule_triggered
    )
    state.load_persistent_rules()
    state.load_persistent_actuators()

    rabbit_thread = threading.Thread(target=start_consuming, args=(state,), daemon=True)
    rabbit_thread.start()

    print("[*] Processing Engine API in avvio sulla porta 8001...")
    app.run(host="0.0.0.0", port=8001)