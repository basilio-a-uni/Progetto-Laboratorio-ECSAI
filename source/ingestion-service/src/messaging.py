import pika
import json
import time
import os

# Nome del nostro Exchange di tipo Fanout
EXCHANGE_NAME = 'mars_telemetry_exchange'

def get_connection():
    rabbit_host = os.getenv('RABBITMQ_HOST', 'localhost')
    while True:
        try:
            # Rimosso il print continuo del testing, lo stampiamo solo in caso di errore o successo
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=rabbit_host)
            )
            return connection
        except pika.exceptions.AMQPConnectionError:
            print(" [!] RabbitMQ not yet started. Retry in 5 seconds.")
            time.sleep(5)

def send_message(unified_data):
    connection = get_connection()
    channel = connection.channel()

    # INVECE DI DICHIARARE UNA CODA, DICHIARIAMO UN EXCHANGE DI TIPO FANOUT
    # Questo significa che il broker inoltrerà il messaggio a TUTTE le code 
    # che decideranno di collegarsi a questo exchange.
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='fanout')

    message = json.dumps(unified_data)

    # Pubblichiamo il messaggio sull'Exchange. 
    # routing_key='' perché il fanout ignora le routing key, manda a tutti!
    channel.basic_publish(
        exchange=EXCHANGE_NAME,
        routing_key='', 
        body=message,
    )

    # De-commenta la riga sotto se vuoi vedere tutto il traffico a terminale,
    # ma attento che potrebbe inondare i log!
    # print(f" [x] Pubblicato su Exchange: {message[:50]}...") 
    connection.close()