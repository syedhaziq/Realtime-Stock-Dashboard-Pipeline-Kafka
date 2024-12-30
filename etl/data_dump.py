from confluent_kafka import Consumer, KafkaError
import json
import logging

# Logging setup
LOG_FILE = "confluent_consumer.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

def consumer_config():
    kafka_config = {
    'bootstrap.servers': 'localhost:9092',  # Kafka broker address
    'group.id': 'stock_consumer_group',     # Consumer group ID
    'auto.offset.reset': 'earliest',        # Start from earliest message if no offset is committed
    }

    consumer = Consumer(kafka_config)
    return consumer



topic_name = 'test'  

def consume_data(topic_name, consumer):
    """Consume messages from the given Kafka topic."""
   
    consumer.subscribe([topic_name])

    try:
        logging.info(f"Subscribed to topic: {topic_name}")
        print(f"Subscribed to topic: {topic_name}")

        while True:
            
            msg = consumer.poll(timeout=1.0)  
            
            if msg is None:
                print(f"No message")
                continue  
            
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    
                    logging.warning(f"End of partition reached for {msg.topic()}.")
                else:
                    logging.error(f"Error: {msg.error()}")
                    raise KafkaError(msg.error())
            else:
                
                data = json.loads(msg.value().decode('utf-8'))
                
                # print(f"Consumed message: {data}")
                logging.info(f"Consumed message: {data}")

    except KeyboardInterrupt:
        logging.info("Consumer stopped manually.")
        print("Consumer stopped manually.")
    finally:
        
        consumer.close()
        logging.info("Consumer connection closed.")
        print("Consumer connection closed.")


consume = consumer_config()
consume_data(topic_name,consume)
