import pika
import json
import time
import os

EXCHANGE_NAME = 'mars_telemetry_exchange'

def get_connection():
    rabbit_host = os.getenv('RABBITMQ_HOST', 'localhost')
    while True:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=rabbit_host)
            )
            return connection
        except pika.exceptions.AMQPConnectionError:
            print("[!] RabbitMQ not yet started. Retry in 5 seconds.")
            time.sleep(5)

def send_message(unified_data):
    connection = get_connection()
    channel = connection.channel()

    # fanout -> broadcast messaging
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='fanout')

    message = json.dumps(unified_data)

    channel.basic_publish(
        exchange=EXCHANGE_NAME,
        routing_key='', 
        body=message,
    )

    connection.close()