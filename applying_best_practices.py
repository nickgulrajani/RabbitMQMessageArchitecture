# Author: Nicholas Gulrajani
import pika
import uuid
from contextlib import closing

# Connection and exchange

credentials = pika.PlainCredentials('user', 'password')
parameters = pika.ConnectionParameters('rmq1', 5672, '/', credentials,
                                   heartbeat=600, blocked_connection_timeout=300)  

connection = pika.BlockingConnection(parameters)
channel = connection.channel()
channel.exchange_declare(exchange='app_exchange', exchange_type='topic', durable=True)

# Queues and bindings setup 

channel.queue_declare('task_queue', durable=True)  
channel.queue_bind(exchange='app_exchange', queue='task_queue', routing_key='task')  

dlx_args = {'x-dead-letter-exchange' : 'dlx.exchange'}
channel.queue_declare('dlq', durable=True, arguments=dlx_args)                             

# Message properties

props = pika.BasicProperties(content_type='application/json', 
                             delivery_mode=2,
                             correlation_id=str(uuid.uuid4()))

# Publishing messages                              

message = {'task_type': 'import', 'payload': {'args': [], 'kwargs': {}}}
channel.basic_publish(exchange='app_exchange',
                      properties=props,
                      routing_key='task',
                      body=json.dumps(message))  

# Consuming tasks

def callback(channel, method, properties, body):
    # Process task
    print(f"Received task:{body}")
    channel.basic_ack(delivery_tag=method.delivery_tag)
    
with closing(connection) as conn:
    with conn.channel() as channel:
        channel.basic_consume('task_queue', callback)
        channel.start_consuming()