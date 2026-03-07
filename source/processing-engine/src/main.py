import pika
import json
import os
import time

import database

from entities import State

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
        print(f"Ricevuto dati : {data}\n\n")

        state.update(data)
        

        ch.basic_ack(delivery_tag=method.delivery_tag)
    return callback

def start_consuming(state):
    connection = get_connection()
    channel = connection.channel()

    channel.queue_declare(queue='sensor_data', durable=False)
    
    channel.basic_consume(
        queue='sensor_data', 
        on_message_callback=inject_callback(state), 
        auto_ack=False
    )
    channel.start_consuming()



if __name__ == "__main__":
    database.init_db()
    state = State()
    state.load_persistent_rules()
    state.load_persistent_actuators()
    print(state.current_rules)
    start_consuming(state)