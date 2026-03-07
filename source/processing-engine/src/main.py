import pika
import json
import os
import time

from collections import defaultdict

import database
import sqlite3

class State():
    def __init__(self, sensor_data = {}, current_rules = defaultdict(list)):
        self.sensor_data = sensor_data
        self.current_rules = current_rules

    def load_rules(self):
        conn = sqlite3.connect(os.getenv("DATABASE_URL"))
        cur = conn.cursor()

        cur.execute("SELECT * FROM rules")
        rows = cur.fetchall()

        for row in rows:
            current_rules[row]
            


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
            print(" [!] RabbitMQ not yeat started. Retry in 2 seconds.")
            time.sleep(2)


def callback(ch, method, properties, body):
    data = json.loads(body)
    print(f"Ricevuto dati : {data}\n\n")
    
    # TODO: logica delle regole    

    ch.basic_ack(delivery_tag=method.delivery_tag)


def start_consuming():
    connection = get_connection()
    channel = connection.channel()

    channel.queue_declare(queue='sensor_data', durable=False)
    
    channel.basic_consume(
        queue='sensor_data', 
        on_message_callback=callback, 
        auto_ack=False
    )
    channel.start_consuming()



if __name__ == "__main__":
    state = State()
    database.init_db()
    start_consuming()