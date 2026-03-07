import pika
import json
import os
import time
import threading 
from flask import Flask, request, jsonify 

import database
from entities import State, Rule 

app = Flask(__name__)

def get_connection():
    rabbit_host = os.getenv('RABBITMQ_HOST', 'localhost')
    while True:
        try:
            print("Testing connection to RabbitMQ...")
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
        print(f"Ricevuto dati : {data}")
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
    
    print("[*] Processing Engine in ascolto su RabbitMQ...")
    channel.start_consuming()

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

if __name__ == "__main__":
    database.init_db()
    
    global state
    state = State()
    state.load_persistent_rules()
    state.load_persistent_actuators()
    
    rabbit_thread = threading.Thread(target=start_consuming, args=(state,), daemon=True)
    rabbit_thread.start()
    
    print("[*] Processing Engine API in avvio sulla porta 8001...")
    app.run(host="0.0.0.0", port=8001)