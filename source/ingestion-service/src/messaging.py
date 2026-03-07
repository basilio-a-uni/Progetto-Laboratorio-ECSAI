import pika
import json
import time
import os

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
        except pika.exceptions.AMQPConnectionError:
            print(" [!] RabbitMQ not yeat started. Retry in 2 seconds.")
            time.sleep(2)


def send_message(unified_data):
    connection = get_connection()
    channel = connection.channel()

    channel.queue_declare(queue='sensor_data', durable=False)

    message = json.dumps(unified_data)

    channel.basic_publish(
        exchange='',
        routing_key='sensor_data',
        body=message,
    )

    print(f" [x] Inviato: {message}")
    connection.close()
